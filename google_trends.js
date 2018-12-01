const googleTrends = require('google-trends-api');
const fs = require('fs');

googleTrends.relatedTopics({keyword: process.argv[2]})
.then(function(results){
  fs.writeFile("google_trends.json", results, function(err) {
    if(err) {
        return console.log(err);
    }
    console.log("The file was saved!");
}); 
})
.catch(function(err){
  console.error('Oh no there was an error', err);
});

