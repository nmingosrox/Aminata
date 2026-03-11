def assert_stage(condition: bool, message: str) -> None:
    """
    Assert a stage condition and raise an error if it fails.

    Args:
        condition (bool): Condition to validate.
        message (str): Message describing the stage.

    Returns:
        None
    """
    if not condition:
        raise RuntimeError(f"[FAIL] {message}")
    print(f"[PASS] {message}")

def normalize_impact(value: Any) -> float:
    """
    Normalize an impact value to the range [-1, 1].

    Args:
        value (Any): Impact value (numeric or string like "low", "medium", "high").

    Returns:
        float: Normalized impact score between -1 and 1.
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        if value > 1:
            value = 1.0
        if value < -1:
            value = -1.0
        return float(value)
    if isinstance(value, str):
        key = value.strip().lower()
        if key in {"low", "minor"}:
            return 0.2
        if key in {"medium", "moderate"}:
            return 0.5
        if key in {"high", "major"}:
            return 0.8
    return 0.0

if __name__ == "__main__":
    # tests for normalization helper
    normalize_impact(0.4)
    normalize_impact('low')
