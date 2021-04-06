from datetime import datetime
from datetime import timezone

import pytest
from aioresponses import aioresponses
from freezegun import freeze_time
from senor_octopus.sources.whistle import whistle

mock_payload = {
    "pets": [
        {
            "id": 123456,
            "gender": "f",
            "name": "Rex",
            "profile_photo_url_sizes": {
                "60x60": None,
                "100x100": None,
                "200x200": None,
                "750x750": None,
            },
            "realtime_channel": {"channel": "private-dog-123456", "service": "Pusher"},
            "subscription_status": "active",
            "partner_service_status": None,
            "device": {
                "model_id": "W04B",
                "serial_number": "W04-1234567",
                "last_check_in": "2021-03-25T15:52:19-07:00 America/Los_Angeles",
                "firmware_version": "0.47-200807 :: 0.47-200807 :: 0.47-200807",
                "battery_level": 96,
                "battery_status": "on",
                "pending_locate": False,
                "tracking_status": "not_tracking",
                "has_gps": True,
                "requires_subscription": True,
                "flashlight_status": {
                    "state": "off",
                    "pattern": None,
                    "brightness": None,
                },
                "partner_record": None,
            },
            "activity_summary": {
                "activity_start_date": "2020-08-22",
                "activity_enabled": True,
                "current_streak": 0,
                "current_minutes_active": 10,
                "current_minutes_rest": 827,
                "similar_dogs_minutes_active": 44.8529743653839,
                "similar_dogs_minutes_rest": 1083.1920639333,
                "suggested_activity_range_lower": 26.0,
                "suggested_activity_range_upper": 52.0,
                "current_activity_goal": {
                    "minutes": 36,
                    "started_at": "2020-08-22T07:00:00Z",
                    "time_zone": "America/Los_Angeles",
                },
                "upcoming_activity_goal": {
                    "minutes": 36,
                    "started_at": "2020-08-22T07:00:00Z",
                    "time_zone": "America/Los_Angeles",
                },
            },
            "last_location": {
                "latitude": 45.0,
                "longitude": -135.0,
                "timestamp": "2021-03-25T22:52:03Z",
                "uncertainty_meters": 0.0,
                "reason": "back_in_beacon",
                "place": {
                    "distance": 0,
                    "distance_units": "feet",
                    "id": 123456,
                    "status": "in_beacon_range",
                    "units": "feet",
                },
                "description": {
                    "address": "0 Fool's St",
                    "place": "Nowhere",
                    "postcode": "12345",
                    "region": "California",
                    "country": "United States",
                },
            },
            "profile": {
                "breed": {"id": 1870, "name": "Italian Greyhound Mix"},
                "date_of_birth": "2008-05-22",
                "age_in_months": 10,
                "age_in_years": 12,
                "time_zone_name": "America/Los_Angeles",
                "weight": 30.0,
                "weight_type": "pounds",
                "species": "dog",
                "overdue_task_occurrence_count": 4,
                "is_fixed": True,
                "body_condition_score": None,
                "pet_food": None,
            },
        },
    ],
}


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_whistle() -> None:
    with aioresponses() as mock_response:
        mock_response.post(
            "https://app.whistle.com/api/login",
            payload={"auth_token": "XXX"},
        )
        mock_response.get("https://app.whistle.com/api/pets", payload=mock_payload)
        events = [event async for event in whistle("username", "password")]

    print(sorted(events, key=lambda e: e["name"]))
    assert sorted(events, key=lambda e: e["name"]) == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.whistle.Rex.battery_level",
            "value": 96,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.whistle.Rex.battery_status",
            "value": "on",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.whistle.Rex.geohash",
            "value": "c00000000000",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.whistle.Rex.last_check_in",
            "value": "2021-03-25T15:52:19-07:00 America/Los_Angeles",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.whistle.Rex.location",
            "value": (45.0, -135.0),
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.whistle.Rex.tracking_status",
            "value": "not_tracking",
        },
    ]
