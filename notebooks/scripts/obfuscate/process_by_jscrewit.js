var JScrewIt = require("jscrewit"),
  fs = require('fs'),
  js;

js = fs.readFileSync(process.argv[2], {encoding: 'utf8'});

obfuscated_code = JScrewIt.encode(js);

fs.writeFileSync(process.argv[3], obfuscated_code);
