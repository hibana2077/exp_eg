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

def upper_middle_point(points:list[int]) -> tuple[float, float]:
    """
    Calculate the upper middle point between two points A and B.
    
    Args:
        points: List of coordinates, where points[0] is point A and points[1] is point B.

    Returns:
        tuple: Upper middle point coordinates (x, y).
    """
    upper_middle_x = (points[0] + points[2]) / 2
    upper_middle_y = min(points[1], points[3])

    return (upper_middle_x, upper_middle_y)

def one_y_point(points:list[int]) -> tuple[float, float]:
    """
    Get the y-coordinate of the upper point from the list of coordinates.
    
    Args:
        points: List of coordinates, where points[0] is point A and points[1] is point B.

    Returns:
        tuple: Y-coordinate of the upper point (y1, y2).
    """
    return (0, points[1])

def two_y_points(points:list[int]) -> tuple[float, float]:
    """
    Get the two y-coordinates from the list of coordinates.
    
    Args:
        points: List of coordinates, where points[0] is point A and points[1] is point B.

    Returns:
        tuple: Two y-coordinates (y1, y2).
    """
    return (points[1], points[3])

def euclidean_distance(point_a:tuple[float, float], point_b:tuple[float, float]) -> float:
    """
    Calculate the Euclidean distance between two points A and B.
    
    Args:
        point_a: Coordinates of point A (x, y).
        point_b: Coordinates of point B (x, y).

    Returns:
        float: Euclidean distance between point A and point B.
    """
    return math.sqrt((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2)

# Example usage
if __name__ == "__main__":
    # Test example
    title_1 = [72, 619.49, 193.297, 608.742]
    text_1 = [72, 599.431, 540.004, 488.048]
    title_3 = [72, 480.013, 281.359, 469.265]

    process_func = one_y_point

    process_title_1 = process_func(title_1)
    process_text_1 = process_func(text_1)
    process_title_3 = process_func(title_3)
    print(f"Processed title_1: {process_title_1}")
    print(f"Processed text_1: {process_text_1}")
    print(f"Processed title_3: {process_title_3}")

    # Calculate euclidean distances
    dist_text1_to_title1 = euclidean_distance(process_text_1, process_title_1)
    dist_title3_to_title1 = euclidean_distance(process_title_3, process_title_1)
    print("text_1 -> title_1 distance:", dist_text1_to_title1)
    print("title_3 -> title_1 distance:", dist_title3_to_title1)