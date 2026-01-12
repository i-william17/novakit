class SuspiciousScore:

    @staticmethod
    def compute(
        geo_changed: bool,
        device_changed: bool,
        ip_bad: bool,
        brute_force_flag: bool,
    ):
        score = 0
        if geo_changed: score += 3
        if device_changed: score += 2
        if ip_bad: score += 3
        if brute_force_flag: score += 2
        return score
