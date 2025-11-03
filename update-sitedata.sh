# Run export SUPABASE_CLIENT_ANON_KEY=<the API key> in your terminal before running this script

# sessions
echo "Updating sessions data..."
curl --location --request POST "https://data.tech.ieeevis.org/functions/v1/session-list" \
    --header "Authorization: Bearer $SUPABASE_CLIENT_ANON_KEY" \
    | jq '.' > ./sitedata/2025/session_list.json
echo "Updated sessions data"

# posters
echo "\n\n\nUpdating posters data..."
curl --location --request GET "https://data.tech.ieeevis.org/rest/v1/papers?event_prefix=eq.v-poster&order=id.asc&apikey=$SUPABASE_CLIENT_ANON_KEY" \
    | jq '.' > ./sitedata/2025/poster_list.json
echo "Updated posters data"

# papers
echo "\n\n\nUpdating papers data..."
curl --location --request GET "https://data.tech.ieeevis.org/rest/v1/papers?event_prefix=neq.v-poster&order=id.asc&apikey=$SUPABASE_CLIENT_ANON_KEY" \
    | jq '.' > ./sitedata/2025/paper_list.json
echo "Updated papers data"
