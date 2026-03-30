# RESTful Booker API QA Test Cases

**Coverage Synopsis:** Positive, Negative, Boundary Values, and Edge Cases explicitly testing state transitions, security, and the scheduled 10-minute database structural reset phase.

|ID|Category|Testcase Description|Precondition|Test Steps|Expected Result|
|---|---|---|---|---|---|
|TC_001|Positive|Verify successful token generation with valid username and password.|API is running.|1. Send POST request to /auth with valid JSON payload: {"username": "admin", "password": "password123"}.|Response 200 OK. Body contains 'token' string.|
|TC_002|Negative|Verify token generation fails gracefully with incorrect password.|API is running.|1. Send POST request to /auth with invalid password payload.|Response 200 OK. Body contains {"reason": "Bad credentials"}.|
|TC_003|Negative|Verify token generation fails gently when payload is completely empty.|API is running.|1. Send POST request to /auth with {} body.|Response 400 Bad Request or Bad Credentials.|
|TC_004|Boundary|Verify token generation with extremely long username string.|API is running.|1. Send POST request to /auth with 1024-character username.|Response handles cleanly without crashing (e.g. 400 or Bad Credentials).|
|TC_005|Edge Case|Verify content-type header strictness on token generation.|API is running.|1. Send POST request to /auth but with Content-Type: text/plain.|Response 415 Unsupported Media Type or equivalent rejection.|
|TC_006|Positive|Verify retrieval of all bookings.|API running, bookings exist.|1. Send GET request to /booking.|Response 200 OK. Returns array of bookingid objects.|
|TC_007|Positive|Verify filtering bookings by exact firstname and lastname matching.|API running, 'sally brown' exists.|1. Send GET request to /booking?firstname=sally&lastname=brown.|Response 200 OK. Returns matched bookingid.|
|TC_008|Negative|Verify filtering by non-existent names returns empty array.|API running.|1. Send GET request to /booking?firstname=NonExistent.|Response 200 OK. Returns [].|
|TC_009|Boundary|Verify date matching filtering explicitly on boundary dates.|Booking with checkin 2018-01-01 exists.|1. Send GET request to /booking?checkin=2018-01-01.|Response 200 OK. Returns bookingid where checkin date >= 2018-01-01.|
|TC_010|Edge Case|Verify filter behavior when checkin parameter > checkout parameter.|API running.|1. Send GET request to /booking?checkin=2020-01-01&checkout=2015-01-01.|Response 400 Bad Request or explicitly empty [].|
|TC_011|Positive|Verify retrieving a booking by a valid existing ID.|Booking exists.|1. Send GET /booking/1 with Accept: application/json.|Response 200 OK. Returns full booking object.|
|TC_012|Negative|Verify retrieving a booking by non-existent numeric ID.|Booking ID does not exist.|1. Send GET /booking/999999999.|Response 404 Not Found.|
|TC_013|Edge Case|Verify retrieving a booking using string/invalid ID path.|API is running.|1. Send GET /booking/invalidID.|Response 404 Not Found or 400 Bad Request.|
|TC_014|Positive|Verify retrieving booking data structurally in XML format.|Booking exists.|1. Send GET /booking/1 with Accept: application/xml.|Response 200 OK. Body is structurally valid XML content.|
|TC_015|Positive|Verify creating a booking with all mandatory and optional fields successfully.|API is running.|1. Send POST /booking with full valid JSON layout.|Response 200 OK. Returns created bookingid and full object.|
|TC_016|Negative|Verify creating a booking fails if mandatory 'totalprice' is completely omitted.|API is running.|1. Send POST /booking missing totalprice field.|Response 400 Bad Request or Explicit Server Error (500).|
|TC_017|Boundary|Verify creating booking with max-integer price bounds.|API is running.|1. Send POST /booking with totalprice: 9999999.|Response 200 OK. Persists extremely high numeric total.|
|TC_018|Boundary|Verify creating booking with negative totalprice.|API is running.|1. Send POST /booking with totalprice: -100.|Response 400 Bad Request, verifying boundary logic enforcement.|
|TC_019|Edge Case|Verify creating booking with strict Date Format violations.|API is running.|1. Send POST /booking checkin: '31-12-2020' instead of 'YYYY-MM-DD'.|Response catches parsing error cleanly.|
|TC_020|Edge Case|Verify booking creation resilience with improper variable types (depositpaid as string).|API is running.|1. Send POST /booking with depositpaid: 'true' (string vs int).|Response handles type-cast or throws 400 Bad Request.|
|TC_021|Positive|Verify successful full state update utilizing valid Cookie Token authorization.|Booking exists. Token obtained.|1. Send PUT /booking/1 with Cookie: token=<token> and modified body.|Response 200 OK. Fully updated record returned.|
|TC_022|Negative|Verify update strictly rejected with entirely missing Auth Header.|Booking exists.|1. Send PUT /booking/1 without Cookie/Basic Auth and valid body.|Response 403 Forbidden.|
|TC_023|Negative|Verify update strictly rejected utilizing an expired or invalid Token.|Booking exists.|1. Send PUT /booking/1 with Cookie: token=invalid.|Response 403 Forbidden.|
|TC_024|Positive|Verify partial field updates apply without overwriting uncalled fields.|Booking exists. Token obtained.|1. Send PATCH /booking/1 with Cookie: token=<token>. Body: {"firstname": "James"}.|Response 200 OK. Only 'firstname' updated, rest persists.|
|TC_025|Boundary|Verify partial update with extremely long name string inputs.|Booking exists. Token obtained.|1. Send PATCH /booking/1 with "firstname": "A"*500.|Response evaluates length cap (400 Bad Request or persists string).|
|TC_026|Positive|Verify successful deletion of target booking with proper authorization.|Booking exists. Token obtained.|1. Send DELETE /booking/1 with Cookie: token=<token>.|Response 201 Created (specific to spec design).|
|TC_027|Negative|Verify deletion mechanism rejects unauthenticated attempts.|Booking exists.|1. Send DELETE /booking/1 with no Auth header.|Response 403 Forbidden.|
|TC_028|Edge Case|Verify system behavior upon attempting to delete an already deleted resource.|Booking previously deleted.|1. Send DELETE /booking/1 with Auth twice sequentially.|Response 405 Method Not Allowed or 404 Not Found.|
|TC_029|Edge Case|Verify background architectural resets (Every 10 minutes DB reset).|State: Initialized. Booking X exists.|1. DELETE Booking X.
2. Wait >10 minutes.
3. Poll for Booking X.|Database cache structurally restarts. Deleted record X reappears via reset vector.|
