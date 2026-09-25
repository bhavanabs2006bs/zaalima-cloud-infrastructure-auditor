from unittest.mock import MagicMock, patch

from cloud_auditor.utils import parse_region_list


def test_parse_region_list_from_argument():
    """Test parsing comma-separated regions."""

    session = MagicMock()

    regions = parse_region_list(
        "us-east-1, us-west-2, ap-south-1",
        session
    )

    assert regions == [
        "us-east-1",
        "us-west-2",
        "ap-south-1",
    ]


@patch("cloud_auditor.utils.get_all_aws_regions")
def test_parse_region_list_discovers_regions_when_empty(mock_get_regions):
    """Test automatic region discovery when no regions are supplied."""

    mock_get_regions.return_value = [
        "us-east-1",
        "ap-south-1",
    ]

    session = MagicMock()

    regions = parse_region_list(None, session)

    mock_get_regions.assert_called_once_with(session)

    assert regions == [
        "us-east-1",
        "ap-south-1",
    ]