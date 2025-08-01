Talent Pool Management API Documentation

  Overview

  The Talent Pool Management system allows mentors to view available
  talents, select talents they want to work with, and reject talents they
  don't want to work with. The system automatically manages mentor-specific
   talent pools and removes talents when they are selected or rejected.

  ---
  1. Get Available Talents (Talent Pool)

  Endpoint: GET /mentor/available-talents-with-posts/

  Description: Returns all talents available in the authenticated mentor's      
  talent pool with their profiles and posts.

  Authentication: Required (JWT Token)

  Headers:
  Authorization: Bearer <jwt_token>
  Content-Type: application/json

  Request Parameters: None (uses authenticated user)

  Response Format:
  [
    {
      "talent": {
        "id": 1,
        "user": {
          "id": 10,
          "username": "john_talent",
          "email": "john@example.com",
          "firstname": "John",
          "lastname": "Doe",
          "gender": "male",
          "age": 25,
          "user_type": "talent",
          "phone_number": "+1234567890",
          "full_name": "John Doe",
          "is_superuser": false,
          "is_staff": false,
          "is_active": true,
          "date_joined": "2024-01-01T00:00:00Z",
          "last_login": "2024-01-15T10:30:00Z",
          "avatar_url": "https://example.com/avatar.jpg"
        },
        "bio": "Passionate football player with 5 years experience",
        "date_of_birth": "1999-03-15",
        "location": "New York, NY",
        "city": "New York",
        "state": "NY",
        "country": "USA",
        "selected_sports": ["football", "basketball"],
        "experience_years": 5,
        "profile_picture": "/media/talent/profiles/john_profile.jpg",
        "cover_photo": "/media/talent/covers/john_cover.jpg",
        "is_verified": true,
        "is_featured": false,
        "social_links": {
          "instagram": "https://instagram.com/johndoe",
          "facebook": "https://facebook.com/johndoe"
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T12:00:00Z"
      },
      "posts": [
        {
          "id": 1,
          "talent": 1,
          "content": "Training hard for the upcoming season!",
          "image": "/media/posts/images/training_session.jpg",
          "video": null,
          "caption": "Morning workout complete",
          "created_at": "2024-01-15T08:00:00Z",
          "updated_at": "2024-01-15T08:00:00Z",
          "likes_count": 25,
          "views_count": 150
        }
      ]
    }
  ]

  Error Responses:
  // 401 Unauthorized
  {
    "detail": "Authentication credentials were not provided."
  }

  // 403 Forbidden (if user is not a mentor)
  {
    "error": "Only mentors can access talent pool."
  }

  ---
  2. Select Talent

  Endpoint: POST /mentor/selected-talents/add/

  Description: Allows a mentor to select a talent. This creates a
  mentor-talent relationship, removes the talent from the mentor's pool,        
  and creates a chat room.

  Authentication: Not required (uses user_id parameter)

  Request Body:
  {
    "user_id": 123,  // Mentor User ID
    "talent_id": 456 // Talent User ID
  }

  Response Format:
  {
    "id": 1,
    "mentor": 123,
    "talent": 456,
    "selected_at": "2024-01-15T14:30:00Z",
    "talent_profile": {
      "id": 1,
      "user": {
        "id": 456,
        "username": "jane_talent",
        "email": "jane@example.com",
        "firstname": "Jane",
        "lastname": "Smith",
        "gender": "female",
        "age": 23,
        "user_type": "talent",
        "phone_number": "+1234567891",
        "full_name": "Jane Smith",
        "is_superuser": false,
        "is_staff": false,
        "is_active": true,
        "date_joined": "2024-01-01T00:00:00Z",
        "last_login": "2024-01-15T10:00:00Z",
        "avatar_url": "https://example.com/jane_avatar.jpg"
      },
      "bio": "Professional tennis player",
      "date_of_birth": "2001-07-20",
      "location": "Los Angeles, CA",
      "city": "Los Angeles",
      "state": "CA",
      "country": "USA",
      "selected_sports": ["tennis", "badminton"],
      "experience_years": 8,
      "profile_picture": "/media/talent/profiles/jane_profile.jpg",
      "cover_photo": null,
      "is_verified": true,
      "is_featured": true,
      "social_links": {
        "instagram": "https://instagram.com/janetennis"
      },
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-10T15:00:00Z"
    },
    "mentor_profile": {
      "id": 1,
      "user": {
        "id": 123,
        "username": "coach_mike",
        "email": "mike@example.com",
        "firstname": "Mike",
        "lastname": "Johnson",
        "gender": "male",
        "age": 35,
        "user_type": "mentor",
        "phone_number": "+1234567892",
        "full_name": "Mike Johnson",
        "is_superuser": false,
        "is_staff": false,
        "is_active": true,
        "date_joined": "2023-12-01T00:00:00Z",
        "last_login": "2024-01-15T09:00:00Z",
        "avatar_url": "https://example.com/mike_avatar.jpg"
      },
      "bio": "Experienced sports coach with 10+ years",
      "date_of_birth": "1989-05-10",
      "location": "Los Angeles, CA",
      "city": "Los Angeles",
      "state": "CA",
      "country": "USA",
      "selected_sports": ["tennis", "football"],
      "coaching_experience_years": 12,
      "playing_experience_years": 15,
      "coaching_levels": "professional",
      "social_links": {
        "linkedin": "https://linkedin.com/in/mikejohnson"
      },
      "coaching_style": "performance_based",
      "max_students": 15,
      "profile_picture": "/media/mentor/profiles/mike_profile.jpg",
      "availability": "full_time",
      "is_verified": true,
      "is_featured": false,
      "is_available": true,
      "created_at": "2023-12-01T00:00:00Z",
      "updated_at": "2024-01-10T11:00:00Z"
    },
    "posts": [
      {
        "id": 2,
        "talent": 1,
        "content": "Just won my local tournament!",
        "image": "/media/posts/images/tournament_win.jpg",
        "video": null,
        "caption": "Victory feels amazing",
        "created_at": "2024-01-14T16:00:00Z",
        "updated_at": "2024-01-14T16:00:00Z",
        "likes_count": 45,
        "views_count": 230
      }
    ],
    "chat_room_id": "550e8400-e29b-41d4-a716-446655440000",
    "can_chat": true
  }

  Error Responses:
  // 400 Bad Request (missing parameters)
  {
    "error": "user_id and talent_id are required."
  }

  // 404 Not Found (user not found)
  {
    "error": "Mentor or Talent user not found."
  }

  // 400 Bad Request (validation errors)
  {
    "mentor": ["This field is required."],
    "talent": ["This field is required."]
  }

  ---
  3. Reject Talent

  Endpoint: POST  /mentor/rejected-talents/add/

  Description: Allows a mentor to reject a talent. This removes the talent      
  from the mentor's pool and sends a notification to the talent.

  Authentication: Not required (uses user_id parameter)

  Request Body:
  {
    "user_id": 123,  // Mentor User ID
    "talent_id": 456 // Talent User ID
  }

  Response Format:
  {
    "id": 1,
    "mentor": 123,
    "talent": 456,
    "rejected_at": "2024-01-15T14:45:00Z",
    "talent_profile": {
      "id": 2,
      "user": {
        "id": 789,
        "username": "alex_talent",
        "email": "alex@example.com",
        "firstname": "Alex",
        "lastname": "Brown",
        "gender": "male",
        "age": 22,
        "user_type": "talent",
        "phone_number": "+1234567893",
        "full_name": "Alex Brown",
        "is_superuser": false,
        "is_staff": false,
        "is_active": true,
        "date_joined": "2024-01-02T00:00:00Z",
        "last_login": "2024-01-15T08:00:00Z",
        "avatar_url": "https://example.com/alex_avatar.jpg"
      },
      "bio": "Basketball enthusiast and player",
      "date_of_birth": "2002-11-08",
      "location": "Chicago, IL",
      "city": "Chicago",
      "state": "IL",
      "country": "USA",
      "selected_sports": ["basketball", "volleyball"],
      "experience_years": 4,
      "profile_picture": "/media/talent/profiles/alex_profile.jpg",
      "cover_photo": "/media/talent/covers/alex_cover.jpg",
      "is_verified": false,
      "is_featured": false,
      "social_links": {},
      "created_at": "2024-01-02T00:00:00Z",
      "updated_at": "2024-01-12T14:00:00Z"
    },
    "mentor_profile": {
      "id": 1,
      "user": {
        "id": 123,
        "username": "coach_mike",
        "email": "mike@example.com",
        "firstname": "Mike",
        "lastname": "Johnson",
        "gender": "male",
        "age": 35,
        "user_type": "mentor",
        "phone_number": "+1234567892",
        "full_name": "Mike Johnson",
        "is_superuser": false,
        "is_staff": false,
        "is_active": true,
        "date_joined": "2023-12-01T00:00:00Z",
        "last_login": "2024-01-15T09:00:00Z",
        "avatar_url": "https://example.com/mike_avatar.jpg"
      },
      "bio": "Experienced sports coach with 10+ years",
      "date_of_birth": "1989-05-10",
      "location": "Los Angeles, CA",
      "city": "Los Angeles",
      "state": "CA",
      "country": "USA",
      "selected_sports": ["tennis", "football"],
      "coaching_experience_years": 12,
      "playing_experience_years": 15,
      "coaching_levels": "professional",
      "social_links": {
        "linkedin": "https://linkedin.com/in/mikejohnson"
      },
      "coaching_style": "performance_based",
      "max_students": 15,
      "profile_picture": "/media/mentor/profiles/mike_profile.jpg",
      "availability": "full_time",
      "is_verified": true,
      "is_featured": false,
      "is_available": true,
      "created_at": "2023-12-01T00:00:00Z",
      "updated_at": "2024-01-10T11:00:00Z"
    },
    "posts": [
      {
        "id": 3,
        "talent": 2,
        "content": "Practice makes perfect!",
        "image": null,
        "video": "/media/posts/videos/practice_session.mp4",
        "caption": "Working on my shots",
        "created_at": "2024-01-13T19:00:00Z",
        "updated_at": "2024-01-13T19:00:00Z",
        "likes_count": 12,
        "views_count": 85
      }
    ]
  }

  Error Responses:
  // 400 Bad Request (missing parameters)
  {
    "error": "user_id and talent_id are required."
  }

  // 404 Not Found (user not found)
  {
    "error": "Mentor or Talent user not found."
  }

  // 400 Bad Request (validation errors)
  {
    "mentor": ["This field is required."],
    "talent": ["This field is required."]
  }

  ---
  4. List Selected Talents

  Endpoint: GET  /mentor/selected-talents/?user_id=123

  Description: Returns all talents that have been selected by a specific        
  mentor.

  Authentication: Not required

  Request Parameters:
  - user_id (required): Mentor User ID

  Response Format:
  [
    {
      "id": 1,
      "mentor": 123,
      "talent": 456,
      "selected_at": "2024-01-15T14:30:00Z",
      "talent_profile": {
        "id": 1,
        "user": {
          "id": 456,
          "username": "jane_talent",
          "email": "jane@example.com",
          "firstname": "Jane",
          "lastname": "Smith",
          "full_name": "Jane Smith",
          "user_type": "talent"
        },
        "bio": "Professional tennis player",
        "selected_sports": ["tennis", "badminton"],
        "experience_years": 8,
        "is_verified": true
      },
      "mentor_profile": {
        "id": 1,
        "user": {
          "id": 123,
          "username": "coach_mike",
          "email": "mike@example.com",
          "firstname": "Mike",
          "lastname": "Johnson",
          "full_name": "Mike Johnson",
          "user_type": "mentor"
        },
        "coaching_experience_years": 12,
        "coaching_style": "performance_based"
      },
      "posts": [
        {
          "id": 2,
          "content": "Just won my local tournament!",
          "image": "/media/posts/images/tournament_win.jpg",
          "likes_count": 45,
          "views_count": 230,
          "created_at": "2024-01-14T16:00:00Z"
        }
      ],
      "chat_room_id": "550e8400-e29b-41d4-a716-446655440000",
      "can_chat": true
    }
  ]

  Error Responses:
  // 400 Bad Request (missing user_id)
  {
    "error": "user_id query parameter is required."
  }

  // 404 Not Found (mentor not found)
  {
    "error": "Mentor user not found."
  }

  ---
  5. List Rejected Talents

  Endpoint: GET  /mentor/rejected-talents/?user_id=123

  Description: Returns all talents that have been rejected by a specific        
  mentor.

  Authentication: Not required

  Request Parameters:
  - user_id (required): Mentor User ID

  Response Format:
  [
    {
      "id": 1,
      "mentor": 123,
      "talent": 789,
      "rejected_at": "2024-01-15T14:45:00Z",
      "talent_profile": {
        "id": 2,
        "user": {
          "id": 789,
          "username": "alex_talent",
          "email": "alex@example.com",
          "firstname": "Alex",
          "lastname": "Brown",
          "full_name": "Alex Brown",
          "user_type": "talent"
        },
        "bio": "Basketball enthusiast and player",
        "selected_sports": ["basketball", "volleyball"],
        "experience_years": 4,
        "is_verified": false
      },
      "mentor_profile": {
        "id": 1,
        "user": {
          "id": 123,
          "username": "coach_mike",
          "email": "mike@example.com",
          "firstname": "Mike",
          "lastname": "Johnson",
          "full_name": "Mike Johnson",
          "user_type": "mentor"
        },
        "coaching_experience_years": 12,
        "coaching_style": "performance_based"
      },
      "posts": [
        {
          "id": 3,
          "content": "Practice makes perfect!",
          "video": "/media/posts/videos/practice_session.mp4",
          "likes_count": 12,
          "views_count": 85,
          "created_at": "2024-01-13T19:00:00Z"
        }
      ]
    }
  ]

  Error Responses:
  // 400 Bad Request (missing user_id)
  {
    "error": "user_id query parameter is required."
  }

  // 404 Not Found (mentor not found)
  {
    "error": "Mentor user not found."
  }

  ---
  6. Get Mentors Who Selected Talent

  Endpoint: GET  /mentor/mentors/selected-talent/{user_id}/

  Description: Returns all mentors who have selected a specific talent.

  Authentication: Not required

  URL Parameters:
  - user_id (required): Talent User ID

  Response Format:
  [
    {
      "mentor": {
        "id": 1,
        "user": {
          "id": 123,
          "username": "coach_mike",
          "email": "mike@example.com",
          "firstname": "Mike",
          "lastname": "Johnson",
          "full_name": "Mike Johnson",
          "user_type": "mentor"
        },
        "bio": "Experienced sports coach with 10+ years",
        "coaching_experience_years": 12,
        "coaching_style": "performance_based",
        "is_verified": true
      },
      "selected_at": "2024-01-15T14:30:00Z"
    }
  ]

  Error Responses:
  // 404 Not Found (talent not found)
  {
    "detail": "Talent user not found"
  }

  ---
  System Behavior

  Talent Pool Management

  1. Automatic Pool Management: When talents complete onboarding, they are      
  automatically added to all mentor pools
  2. Selection Removal: When a mentor selects a talent, that talent is
  removed from that mentor's pool only
  3. Rejection Removal: When a mentor rejects a talent, that talent is
  removed from that mentor's pool only
  4. Isolation: Each mentor has their own independent talent pool

  Side Effects

  1. Chat Room Creation: Selecting a talent automatically creates a private     
   chat room
  2. Notifications: Both selection and rejection trigger notifications to       
  the talent
  3. Signal Processing: All pool updates happen automatically via Django        
  signals

  Authentication Notes

  - Available talents endpoint requires JWT authentication
  - Selection/rejection endpoints currently use user_id parameter (can be       
  updated to use authentication)
  - List endpoints are currently public (can be updated to require
  authentication)