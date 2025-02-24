from main import calculate_priority

def test_priority_calculation():
    # Test item
    test_item = {"link": "https://long-domain-name.com/article"}
    
    # Calculate priority
    score = calculate_priority(test_item)
    
    # Assertions
    assert score == len(test_item["link"]) * 0.1
