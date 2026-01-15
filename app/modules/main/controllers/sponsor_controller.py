from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.sessions import get_db

# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/v1/sponsor",
    tags=["Sponsor"]
)

# ============================================================
# DEV MODE (NO AUTH)
# ============================================================

DEV_SPONSOR_ID = 1

# ============================================================
# SCHEMAS
# ============================================================

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    totalBudget: float
    pricePerScan: float
    fundingMethod: str  # escrow | credit_line


class CampaignAssetCreate(BaseModel):
    assetType: str  # image | video
    assetUrl: str


# ============================================================
# CAMPAIGNS
# ============================================================

@router.post("/campaigns", summary="Create campaign (draft)")
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            INSERT INTO acc_campaigns
                (sponsor_id, name, description, total_budget, price_per_scan, funding_method)
            VALUES
                (:sponsor_id, :name, :description, :total_budget, :price_per_scan, :funding_method)
            RETURNING id
        """),
        {
            "sponsor_id": DEV_SPONSOR_ID,
            "name": payload.name,
            "description": payload.description,
            "total_budget": payload.totalBudget,
            "price_per_scan": payload.pricePerScan,
            "funding_method": payload.fundingMethod,
        }
    )

    await db.commit()
    return {"campaignId": result.scalar_one(), "status": "draft"}


@router.post("/campaign-assets/{campaign_id}", summary="Upload campaign asset")
async def upload_campaign_asset(
    campaign_id: int,
    payload: CampaignAssetCreate,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        text("""
            INSERT INTO acc_campaign_assets
                (campaign_id, asset_type, asset_url)
            SELECT id, :asset_type, :asset_url
            FROM acc_campaigns
            WHERE id = :campaign_id
              AND sponsor_id = :sponsor_id
        """),
        {
            "campaign_id": campaign_id,
            "asset_type": payload.assetType,
            "asset_url": payload.assetUrl,
            "sponsor_id": DEV_SPONSOR_ID,
        }
    )

    await db.commit()
    return {"status": "uploaded"}


@router.post("/campaign-submit/{campaign_id}", summary="Submit campaign for approval")
async def submit_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
):
    asset_count = (
        await db.execute(
            text("""
                SELECT COUNT(*)
                FROM acc_campaign_assets a
                JOIN acc_campaigns c ON c.id = a.campaign_id
                WHERE a.campaign_id = :campaign_id
                  AND c.sponsor_id = :sponsor_id
            """),
            {
                "campaign_id": campaign_id,
                "sponsor_id": DEV_SPONSOR_ID,
            },
        )
    ).scalar_one()

    if asset_count == 0:
        raise HTTPException(400, "Upload assets before submitting")

    await db.execute(
        text("""
            UPDATE acc_campaigns
            SET status = 'pending_approval'
            WHERE id = :campaign_id
              AND sponsor_id = :sponsor_id
              AND status = 'draft'
        """),
        {
            "campaign_id": campaign_id,
            "sponsor_id": DEV_SPONSOR_ID,
        }
    )

    await db.commit()
    return {"status": "pending_approval"}


@router.get("/campaigns", summary="List sponsor campaigns with assets")
async def list_campaigns(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = """
        SELECT
            c.id,
            c.name,
            c.status,
            c.total_budget,
            c.price_per_scan,
            c.created_at,
            COALESCE(
                json_agg(
                    json_build_object(
                        'id', a.id,
                        'asset_type', a.asset_type,
                        'asset_url', a.asset_url
                    )
                ) FILTER (WHERE a.id IS NOT NULL),
                '[]'
            ) AS assets
        FROM acc_campaigns c
        LEFT JOIN acc_campaign_assets a
            ON a.campaign_id = c.id
        WHERE c.sponsor_id = :sponsor_id
    """

    params = {"sponsor_id": DEV_SPONSOR_ID}

    if status:
        query += " AND c.status = :status"
        params["status"] = status

    query += """
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """

    result = await db.execute(text(query), params)
    return result.mappings().all()


@router.get("/campaign/{campaign_id}", summary="Campaign detail")
async def campaign_detail(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
):
    campaign = (
        await db.execute(
            text("""
                SELECT *
                FROM acc_campaigns
                WHERE id = :campaign_id
                  AND sponsor_id = :sponsor_id
            """),
            {
                "campaign_id": campaign_id,
                "sponsor_id": DEV_SPONSOR_ID,
            },
        )
    ).mappings().first()

    if not campaign:
        raise HTTPException(404, "Campaign not found")

    return campaign


@router.get("/campaign-scan-evidence/{campaign_id}", summary="Scan evidence")
async def campaign_scan_evidence(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT station_code,
                   latitude,
                   longitude,
                   scan_count,
                   first_scan_at,
                   last_scan_at
            FROM acc_campaign_scan_stats
            WHERE campaign_id = :campaign_id
        """),
        {"campaign_id": campaign_id},
    )

    return result.mappings().all()


# ============================================================
# BILLING
# ============================================================

@router.get("/invoices", summary="List sponsor invoices")
async def list_invoices(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = """
        SELECT id, invoice_ref, total_amount, status, due_date
        FROM acc_invoices
        WHERE sponsor_id = :sponsor_id
    """

    params = {"sponsor_id": DEV_SPONSOR_ID}

    if status:
        query += " AND status = :status"
        params["status"] = status

    result = await db.execute(text(query), params)
    return result.mappings().all()


@router.get("/invoice/{invoice_id}", summary="Invoice detail")
async def invoice_detail(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    invoice = (
        await db.execute(
            text("""
                SELECT *
                FROM acc_invoices
                WHERE id = :invoice_id
                  AND sponsor_id = :sponsor_id
            """),
            {
                "invoice_id": invoice_id,
                "sponsor_id": DEV_SPONSOR_ID,
            },
        )
    ).mappings().first()

    if not invoice:
        raise HTTPException(404, "Invoice not found")

    return invoice


@router.post("/invoice-pay/{invoice_id}", summary="Pay invoice (SEPA)")
async def pay_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            INSERT INTO acc_payment_intents
                (invoice_id, method, status, expected_amount)
            SELECT id, 'sepa', 'pending', total_amount
            FROM acc_invoices
            WHERE id = :invoice_id
              AND sponsor_id = :sponsor_id
            RETURNING id
        """),
        {
            "invoice_id": invoice_id,
            "sponsor_id": DEV_SPONSOR_ID,
        }
    )

    intent_id = result.scalar_one_or_none()
    if not intent_id:
        raise HTTPException(400, "Invoice not payable")

    await db.commit()

    return {
        "paymentIntentId": intent_id,
        "redirectUrl": f"https://pay/checkout/{intent_id}",
    }
