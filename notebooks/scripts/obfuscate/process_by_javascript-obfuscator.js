var JavaScriptObfuscator = require('javascript-obfuscator');
var fs = require('fs');


input_file_path = process.argv[2];

fs.readFile(input_file_path, 'utf8', function(err, input_source) {
    var obfuscationResult = JavaScriptObfuscator.obfuscate(
        input_source,
        {
            compact: false,
            controlFlowFlattening: true
        }
    );

    output_source = obfuscationResult.getObfuscatedCode();

    output_file_path = process.argv[3];
    fs.writeFile(output_file_path, output_source, function(err) {
            if(err) {
                return console.log(err);
            }
    });
});
