from risk.temporal import TemporalAnalyzer


def main():
    analyzer = TemporalAnalyzer()

    print("=" * 60)
    print("SENTINEL TEMPORAL ANALYZER TEST")
    print("=" * 60)

    # --------------------------------------------------
    # TEST 1: EMPTY HISTORY
    # --------------------------------------------------

    print("\n[TEST 1] Empty history")

    result = analyzer.recent_average()

    print("History :", analyzer.get_history())
    print("Average :", result)

    assert result == 0.0

    # --------------------------------------------------
    # TEST 2: SINGLE VALUE
    # --------------------------------------------------

    print("\n[TEST 2] Single anomaly score")

    analyzer.update(0.8)

    print("History :", analyzer.get_history())
    print("Average :", analyzer.recent_average())

    assert analyzer.get_history() == [0.8]
    assert analyzer.recent_average() == 0.8

    # --------------------------------------------------
    # TEST 3: MULTIPLE VALUES
    # --------------------------------------------------

    print("\n[TEST 3] Multiple anomaly scores")

    analyzer.update(0.6)
    analyzer.update(0.4)

    print("History :", analyzer.get_history())
    print("Average :", analyzer.recent_average())

    expected_average = (0.8 + 0.6 + 0.4) / 3

    assert analyzer.recent_average() == expected_average

    # --------------------------------------------------
    # TEST 4: WINDOW SIZE
    # --------------------------------------------------

    print("\n[TEST 4] Temporal window")

    analyzer.update(0.2)
    analyzer.update(0.3)
    analyzer.update(0.9)

    history = analyzer.get_history()

    print("History :", history)
    print("Length  :", len(history))
    print("Average :", analyzer.recent_average())

    assert len(history) == 5

    # --------------------------------------------------
    # TEST 5: OLD VALUE REMOVED
    # --------------------------------------------------

    print("\n[TEST 5] Oldest value removed")

    analyzer.update(0.7)

    history = analyzer.get_history()

    print("History :", history)
    print("Length  :", len(history))

    assert len(history) == 5
    assert history == [0.4, 0.2, 0.3, 0.9, 0.7]

    # --------------------------------------------------
    # TEST 6: CLAMPING
    # --------------------------------------------------

    print("\n[TEST 6] Score clamping")

    analyzer = TemporalAnalyzer()

    analyzer.update(1.5)
    analyzer.update(-0.5)

    history = analyzer.get_history()

    print("Input values : 1.5, -0.5")
    print("Stored values:", history)

    assert history == [1.0, 0.0]

    # --------------------------------------------------
    # FINAL
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ALL TEMPORAL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()