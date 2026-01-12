from typing import List, Dict, Any


class BaseMenu:
    """
    BaseMenu.
    Handles permission filtering and menu transformations.
    """

    def __init__(self, permissions: List[str] = None):
        self.permissions = permissions or []

    def menus(self) -> List[Dict[str, Any]]:
        """ Should be implemented by child classes """
        raise NotImplementedError("menus() must be implemented in subclass")

    def check_rights(self, permission: str) -> bool:
        """Check if user has permission."""
        return permission in self.permissions

    def load_menus(self) -> List[Dict[str, Any]]:
        """Filter and clean up menus"""
        processed = []

        for item in self.menus():
            if "visible" in item and not item["visible"]:
                continue

            # handle submenus
            if "submenus" in item:
                sub = []
                for s in item["submenus"]:
                    if "visible" in s and not s["visible"]:
                        continue
                    s.pop("visible", None)
                    sub.append(s)

                if not sub:
                    continue

                item["submenus"] = sub

            # remove visibility key
            item.pop("visible", None)

            processed.append(item)

        return processed
