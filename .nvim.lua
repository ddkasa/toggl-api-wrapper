table.insert(require("dap").configurations.python, {
	type = "python",
	request = "launch",
	name = "debug file",
	program = "${file}",
})

function paste_in_official_docs()
	local pos = vim.api.nvim_win_get_cursor(0)[2]
	local line = vim.api.nvim_get_current_line()
	local clipboard_content = vim.fn.getreg("+")
	local nline = line:sub(0, pos) .. "[Official Documentation](" .. clipboard_content .. ")" .. line:sub(pos + 1)
	vim.api.nvim_set_current_line(nline)
end
