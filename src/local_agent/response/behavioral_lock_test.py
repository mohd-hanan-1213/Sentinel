from response.behavioral_lock import BehavioralLock


def main():
    lock = BehavioralLock()

    print("=" * 60)
    print("SENTINEL BEHAVIORAL LOCK TEST")
    print("=" * 60)

    # --------------------------------------------------
    # TEST 1: INITIAL STATE
    # --------------------------------------------------

    print("\n[TEST 1] Initial state")

    print("State :", lock.get_state())
    print("Locked:", lock.is_locked())

    assert lock.get_state() == "UNLOCKED"
    assert lock.is_locked() is False

    # --------------------------------------------------
    # TEST 2: ACTIVATE LOCK
    # --------------------------------------------------

    print("\n[TEST 2] Activate behavioral lock")

    lock.lock()

    print("State :", lock.get_state())
    print("Locked:", lock.is_locked())

    assert lock.get_state() == "LOCKED"
    assert lock.is_locked() is True

    # --------------------------------------------------
    # TEST 3: WRONG SENTINEL PASSWORD
    # --------------------------------------------------

    print("\n[TEST 3] Failed Sentinel recovery")

    result = lock.recover(
        username="AswinKB",
        password="WRONG_PASSWORD",
    )

    print("Recovery successful:", result)
    print("State              :", lock.get_state())
    print("Locked             :", lock.is_locked())

    assert result is False
    assert lock.is_locked() is True

    # --------------------------------------------------
    # TEST 4: CORRECT SENTINEL PASSWORD
    # --------------------------------------------------

    print("\n[TEST 4] Successful Sentinel recovery")

    username = input("Enter Sentinel admin username: ")
    password = input("Enter Sentinel admin password: ")

    result = lock.recover(
        username=username,
        password=password,
    )

    print("Recovery successful:", result)
    print("State              :", lock.get_state())
    print("Locked             :", lock.is_locked())

    assert result is True
    assert lock.is_locked() is False

    # --------------------------------------------------
    # FINAL
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ALL BEHAVIORAL LOCK TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()