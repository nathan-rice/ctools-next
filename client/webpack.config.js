var path = require("path");
module.exports = {
    entry: "./init.js",
    output: {
        path: path.resolve(__dirname, "build"),
        filename: "bundle.js"
    },
    module: {
        loaders: [
            { test: /\.css$/, loader: "style!css" }
        ]
    },
    resolve: {
        modulesDirectories: ["node_modules", "", "components"]
    }
};
