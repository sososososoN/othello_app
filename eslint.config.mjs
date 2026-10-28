
import js from "@eslint/js";
import globals from "globals";

export default [
    {
        ignores: [
            "node_modules/**",
            "coverage/**",
        ],
    },
    {
        files: ["static/js/**/*.js"],
        languageOptions: {
            globals: globals.browser,
            ecmaVersion: "latest",
        },
        rules: {
            ...js.configs.recommended.rules,
        },
    },
    {
        files: ["tests/**/*.js"],
        languageOptions: {
            globals: {
                ...globals.browser,
                ...globals.node,
            },
            ecmaVersion: "latest",
        },
        rules: {
            ...js.configs.recommended.rules,
        },
    },
];
