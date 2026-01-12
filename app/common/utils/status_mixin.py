from typing import Dict, Tuple

class StatusMixin:
    """
    Port of novatron novakit utilsStatus

    Usage:
        mixin = StatusMixin()
        mixin.load_status("SC10")  # -> {'label': 'Active', 'theme': 'success'}

    You can subclass or instantiate. Methods are stateless.
    """

    def load_status(self, code: str) -> Dict[str, str]:
        codes = {**self.app_codes(), **self.core_codes()}
        result = codes.get(code, [f"unknown code: {code}", "secondary"])
        return {"label": result[0], "theme": result[1]}

    def app_codes(self) -> dict:
        return {
            "SC0": ["False", "danger"],
            "SC1": ["True", "success"],
            "SC2": ["Approved", "success"],
            "SC3": ["Pending", "info"],
            "SC4": ["Cancelled", "warning"],
            "SC5": ["Declined", "danger"],
            "SC6": ["Banned", "danger"],
            "SC7": ["Suspended", "warning"],
            "SC8": ["Scheduled", "info"],
            "SC9": ["Inactive", "secondary"],
            "SC10": ["Active", "success"],
            "SC11": ["Re-Scheduled", "info"],
        }

    def core_codes(self) -> dict:
        return {
            "SC100": ["Continue", "info"],
            "SC101": ["Switching Protocols", "info"],
            "SC103": ["Early Hints", "info"],
            "SC200": ["OK", "success"],
            "SC201": ["Created", "success"],
            "SC202": ["Accepted", "success"],
            "SC203": ["Non-Authoritative Information", "success"],
            "SC204": ["No Content", "info"],
            "SC205": ["Reset Content", "success"],
            "SC206": ["Partial Content", "info"],
            "SC207": ["Multi-Status", "success"],
            "SC226": ["IM Used", "success"],
            "SC300": ["Multiple Choices", "danger"],
            "SC301": ["Moved Permanently", "danger"],
            "SC302": ["Found", "danger"],
            "SC303": ["See Other", "danger"],
            "SC304": ["Not Modified", "danger"],
            "SC305": ["Use Proxy", "danger"],
            "SC306": ["Reserved", "danger"],
            "SC307": ["Temporary Redirect", "danger"],
            "SC400": ["Bad Request", "danger"],
            "SC401": ["Unauthorized", "danger"],
            "SC402": ["Payment Required", "danger"],
            "SC403": ["Forbidden", "danger"],
            "SC404": ["Not Found", "danger"],
            "SC405": ["Method Not Allowed", "danger"],
            "SC406": ["Not Acceptable", "danger"],
            "SC407": ["Proxy Authentication Required", "danger"],
            "SC408": ["Request Timeout", "danger"],
            "SC409": ["Conflict", "danger"],
            "SC410": ["Gone", "danger"],
            "SC411": ["Length Required", "danger"],
            "SC412": ["Precondition Failed", "danger"],
            "SC413": ["Request Entity Too Large", "danger"],
            "SC414": ["Request-URI Too Long", "danger"],
            "SC415": ["Unsupported Media Type", "danger"],
            "SC416": ["Requested Range Not Satisfiable", "danger"],
            "SC417": ["Expectation Failed", "danger"],
            "SC422": ["Unprocessable Entity", "danger"],
            "SC423": ["Locked", "danger"],
            "SC424": ["Failed Dependency", "danger"],
            "SC426": ["Upgrade Required", "danger"],
            "SC500": ["Internal Server Error", "danger"],
            "SC501": ["Not Implemented", "danger"],
            "SC502": ["Bad Gateway", "danger"],
            "SC503": ["Service Unavailable", "danger"],
            "SC504": ["Gateway Timeout", "danger"],
            "SC505": ["HTTP Version Not Supported", "danger"],
            "SC506": ["Variant Also Negotiates", "danger"],
            "SC507": ["Insufficient Storage", "danger"],
            "SC510": ["Not Extended", "danger"],
        }
