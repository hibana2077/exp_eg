import math

def calculate_centroid(points:list[int]) -> tuple[float, float]:
    """
    Calculate the centroid (midpoint) of two points A and B.
    
    Args:
        points: List of coordinates, where points[0] is point A and points[1] is point B.

    Returns:
        tuple: Centroid coordinates (centroid_x, centroid_y).
    """
    centroid_x = (points[0] + points[2]) / 2
    centroid_y = (points[1] + points[3]) / 2

    return [centroid_x, centroid_y]

def get_first_point(points:list[int]) -> tuple[float, float]:
    """
    Get the first point A from the list of coordinates.
    
    Args:
        points: List of coordinates, where points[0] is point A and points[1] is point B.

    Returns:
        tuple: Coordinates of point A (x, y).
    """
    return (points[0], points[1])

def get_second_point(points:list[int]) -> tuple[float, float]:
    """
    Get the second point B from the list of coordinates.

    Args:
        points: List of coordinates, where points[0] is point A and points[1] is point B.

    Returns:
        tuple: Coordinates of point B (x, y).
    """
    return (points[2], points[3])


# Example usage
if __name__ == "__main__":
    # Test example
    points = [72, 619, 193, 608]
    centroid = calculate_centroid(points)
    print(f"The centroid of point A{points[:2]} and point B{points[2:]} is: {centroid}")