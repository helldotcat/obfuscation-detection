var gnirts = require('gnirts'),
  fs = require('fs'),
  js;

js = fs.readFileSync(process.argv[2], {encoding: 'utf8'});

obfuscated_code = gnirts.getCode(js);

fs.writeFileSync(process.argv[3], obfuscated_code);