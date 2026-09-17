from security.access_control import AccessController


def main():
    controller = AccessController()

    print("=" * 60)
    print("SENTINEL ACCESS CONTROL TEST")
    print("=" * 60)

    username = input("Enter Sentinel admin username: ")
    password = input("Enter Sentinel admin password: ")

    # --------------------------------------------------
    # TEST 1: ADMIN DASHBOARD
    # --------------------------------------------------

    print("\n[TEST 1] Admin Dashboard Access")

    result = controller.authorize_admin_dashboard(
        username=username,
        password=password,
    )

    print("Allowed :", result.allowed)
    print("Username:", result.username)
    print("Role    :", result.role)
    print("Message :", result.message)

    # --------------------------------------------------
    # TEST 2: BEHAVIORAL LOCK RECOVERY
    # --------------------------------------------------

    print("\n[TEST 2] Behavioral Lock Recovery")

    result = controller.authorize_behavioral_lock_recovery(
        username=username,
        password=password,
    )

    print("Allowed :", result.allowed)
    print("Username:", result.username)
    print("Role    :", result.role)
    print("Message :", result.message)

    # --------------------------------------------------
    # TEST 3: SECURITY EVIDENCE
    # --------------------------------------------------

    print("\n[TEST 3] Security Evidence Access")

    result = controller.authorize_security_evidence(
        username=username,
        password=password,
    )

    print("Allowed :", result.allowed)
    print("Username:", result.username)
    print("Role    :", result.role)
    print("Message :", result.message)


if __name__ == "__main__":
    main()