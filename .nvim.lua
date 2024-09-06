table.insert(require("dap").configurations.python, {
	type = "python",
	request = "launch",
	name = "debug file",
	program = "${file}",
	-- ... more options, see https://github.com/microsoft/debugpy/wiki/debug-configuration-settings
})
