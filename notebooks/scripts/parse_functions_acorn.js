#!/usr/bin/env node

const acorn = require("acorn")
const walk = require("acorn-walk")

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

    walk.full(acorn.parse(source), node => {
        if (node.type === 'FunctionDeclaration') {
            entries.push({
                start: node.start,
                end: node.end
            });
        }
    });

    entries.forEach(
        function(element) {
            saveFunctionSourceCode(source, output_file_path, element.start, element.end)
        }
    )
});
