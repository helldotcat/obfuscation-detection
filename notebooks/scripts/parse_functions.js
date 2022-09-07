#!/usr/bin/env node

var esprima = require('esprima');
var fs = require('fs');


function saveFunctionSourceCode(source, output_file_path, start_offset, end_offset) {    
    temp_js_filename = output_file_path.slice(0, -3)

    output_file_path = (
        [temp_js_filename, '_',
         start_offset.toString(), '_',
         end_offset.toString(), '.js']
    ).join('')

    function_source_code = source.slice(start_offset, end_offset)

    fs.writeFile(output_file_path, function_source_code, function(err) {
        if(err) {
            return console.log(err);
        }
    });
}
 

input_file_path = process.argv[2]
output_file_path = process.argv[3]

fs.readFile(input_file_path, 'utf8', function(err, source) {
    const entries = [];
    esprima.parseModule(source, { range: true }, function (node, meta) {
        if (node.type === 'FunctionDeclaration') {
            entries.push({
                start: meta.start.offset,
                end: meta.end.offset
            });
        }
    });
    entries.forEach(
        function(element) {
            saveFunctionSourceCode(source, output_file_path, element.start, element.end)
        }
    )
});
