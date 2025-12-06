from app.core.base_menu import BaseMenu

class Menu(BaseMenu):
    module_id = "iam"

    def menus(self):
        return [
            {
                "label": "Dashboard",
                "icon": "paw",
                "route": f"/{self.module_id}/",
                "visible": self.check_rights("iamDashboard"),
            },
            {
                "label": "Profiles",
                "icon": "users",
                "route": f"/{self.module_id}/profiles",
                "visible": self.check_rights("adminProfileList"),
            },
            {
                "label": "Access Control",
                "icon": "shield",
                "route": "#",
                "submenus": [
                    {
                        "label": "Users",
                        "route": f"/{self.module_id}/users",
                        "visible": self.check_rights("iamUsers"),
                    },
                    {
                        "label": "Groups",
                        "route": f"/{self.module_id}/rbac/groups",
                        "visible": self.check_rights("iamGroups"),
                    },
                    {
                        "label": "Roles",
                        "route": f"/{self.module_id}/rbac/roles",
                        "visible": self.check_rights("iamAccessControl"),
                    },
                    {
                        "label": "Permissions",
                        "route": f"/{self.module_id}/rbac/permissions",
                        "visible": self.check_rights("iamAccessControl"),
                    },
                ],
            },
        ]
