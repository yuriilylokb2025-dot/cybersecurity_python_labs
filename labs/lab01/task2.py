users = {
    "security_chief": {
        "role": "security_officer",
        "clearance": 4,
        "department": "Security",
        "active": True,
    },
    "network_admin": {
        "role": "network_admin",
        "clearance": 3,
        "department": "Network",
        "active": True,
    },
    "help_desk": {
        "role": "support",
        "clearance": 1,
        "department": "Support",
        "active": True,
    },
    "auditor_ext": {
        "role": "auditor",
        "clearance": 3,
        "department": "Audit",
        "active": True,
    },
    "temp_worker": {
        "role": "temporary",
        "clearance": 1,
        "department": "Temp",
        "active": False,
    },
}

resources = [
    ("incident_reports", 4),
    ("network_topology", 3),
    ("user_manual", 1),
    ("vulnerability_scans", 3),
    ("root_access", 4),
    ("help_tickets", 1),
    ("penetration_tests", 4),
    ("firewall_rules", 3),
    ("software_licenses", 2),
    ("faq_docs", 1),
]

security_levels = (
    "Unrestricted",
    "Limited",
    "Sensitive",
    "Classified",
)

blocked_users = {
    "temp_worker",
    "fired_employee",
    "compromised_acc",
}


def check_access(username, resource_level):
    if username not in users:
        return "DENY", "User not found"

    if username in blocked_users:
        return "DENY", "User is blocked"

    if users[username]["active"] is False:
        return "DENY", "Account inactive"

    if users[username]["clearance"] >= resource_level:
        return "ALLOW", ""

    return "DENY", "Insufficient clearance"


def main():
    print("Resources:")

    for resource_name, resource_level in resources:
        level_name = security_levels[resource_level - 1]

        print(f"resource={resource_name}, security_level={level_name}")

    print("\nAccess check:")

    for username in users:
        for resource_name, resource_level in resources:
            result, reason = check_access(username, resource_level)

            if result == "ALLOW":
                print(f"user={username} resource={resource_name} -> ALLOW")
            else:
                print(f"user={username} resource={resource_name} -> DENY ({reason})")


if __name__ == "__main__":
    main()
