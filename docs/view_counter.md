# View Counter

Starting in 2022, we implemented a simple view counter for the those streaming the conference from the virtual site.  In 2020, streams were handled directly in youtube.  In 2021, we switched to embedding youtube streams in the virtual vis website, and the view tracking for embedded youtube videos is [unreliable](https://support.google.com/youtube/thread/23699221?hl=en&msgid=23705029).  In 2021, we tried to use a private instance of [matomo](https://matomo.org/) to track live attendee numbers as well as record data to do a post-conference analysis.  However, we found that a large portion of attendees either declined to be tracked or had the matomo tracker blocked altogether by ad-blockers or other such software.

In 2022, we have decided to implement a simple custom polling script that will write active streamer counts to a database that can then be read within discord to give a reasonable live count.  It will use all AWS tools and largely follow a tutorial on [creating a CRUD API.](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-dynamo-db.html) 

## Setup

To set up the view counter, the following steps were taken.

1. Create a DynamoDB instance on the IEEE VIS AWS account
	- name: ieeevis_url_counter
	- partition_key: view_uuid (just a unique identifier that I generate)
	- **I wasn't able to actually create the table because of a permissions issue**.  I got the following error: "User: arn:aws:iam::816627965283:user/ieeevistech@gmail.com is not authorized to perform: dynamodb:CreateTable on resource: arn:aws:dynamodb:us-east-1:816627965283:table/ieeevis_url_counter_test because no identity-based policy allows the dynamodb:CreateTable action".  I think I need to go in as the root user and create a policy that lets ieeevistech@gmail.com create tables on dynamodb.  Probably for the other resources as well.
	- Actually, nevermind.  I just switched to a different user, visweb, and it had permissions.  I guess the ieeevistech@gmail.com is probably just for sending emails.
2. Create lambda function for writing a streaming view to the dynamodb
	- function_name: writeStreamView
	- left it as a node function
	- Under permissions, change default execution role
	- Create new role, name streamViewWriter, template of simple microservice
	- Edited index.js by adding some tutorial code from the CRUD tutorial.  But then modified it so it only had two actions: create, and read.  Create sends the URL path, and a timestamp, and writes it directly to the dynamoDB.  Read takes in a path, and optionally a timestamp.  This counter should be posted by all active streamers every 2 minutes.  Then, the read should occur every 10 minutes, and read the last 4 2-minute intervals, and average out the number of posts that are read.  With no timestamp, it returns the average for the last 4 2-minute intervals.  With a time stamp, it returns the average for the 4 2-minute intervals counting back from the received timestamp.
	- At this point, I realized that DynamoDB was the wrong instance - I don't want a NoSQL db, I want a SQL db, since I don't actually have queryable objects: I just want a collection of timestamps.  I looked into creating an index for the dynamodb instance, but I think that just overcomplicates things.  I want a sql instance with an index on the timestamp.
	- Ok, I've changed my mind.  The key should be the url.  Then there should be a secondary key of the time stamp (current UTC timestamp modded out by 2 minutes).  Then, the counter should be an autoincrement.  I guess we run into atomic issues there.  But maybe we just write a stamp in every time, since we don't want to actually track any data but we can still count that way in a non-transactional way.  I assume dynamodb has some way of atomic pushs into collections.
	- Created a secondary index on url_path and then sorting on view_timestamp.  I _think_ this will work.
3. Create an API Gateway registration
	- api_name: streamViewApi
	- Linked the lambda function as an integration
	- Added routes corresponding to my two methods, a put and a get
4. Tested it out with curl
	- Got the API URL: https://ljiotj1l7f.execute-api.us-east-1.amazonaws.com/
	- Curl to put 
	- Curl to get

		curl -v -X "PUT" -H "Content-Type: application/json" -d "{\"urlPath\": \"abcdef\"}" https://ljiotj1l7f.execute-api.us-east-1.amazonaws.com/streamView

		curl -v -X "GET" -H "Content-Type: application/json" https://ljiotj1l7f.execute-api.us-east-1.amazonaws.com/streamViews/abcdef

It took some messing around, but it all worked.  Now, we need the room stream page to send PUT every 2 minutes starting on page load.  And the discord can read from it every 10 minutes or whatever.  

## How it works

There's an API sitting on AWS called 'streamViewAPI', created by the `visweb` user on the vis AWS account.  It has two methods: a PUT that will get run on the client side every 2 minutes while someone's got one of the rooms pages open, and then a GET that takes in a room ID and returns the number of viewers.  Since it's a measurement of discrete "pollings" of users, it does a little cleanup where the written "views" get a rounded timestamp assigned to them when they are written to the database, and then the GET command picks the max count per rounded timestamp (so at 8:02 AM there are 36 viewers, at 8:04 AM there are 27 viewers, if we poll at 8:05 AM, we will return 36 active viewers).  

The PUT command is run in the javascript on the rooms SHOW page.  The GET command will be run from somewhere external where we are monitoring the users, probably discord.