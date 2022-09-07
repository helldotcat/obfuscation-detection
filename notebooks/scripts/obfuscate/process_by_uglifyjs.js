var UglifyJS = require("uglify-js");
var fs = require('fs');

code = fs.readFileSync(process.argv[2], {encoding: 'utf8'});

var result = UglifyJS.minify(code, {
	mangle: true,
	compress: {
		sequences: true,
		conditionals: true,
		booleans: true,
		if_return: true,
		join_vars: true,
	},
	output: {
        ast: true,
        code: true  // optional - faster if false
    }
}).code;

fs.writeFileSync(process.argv[3], result);
