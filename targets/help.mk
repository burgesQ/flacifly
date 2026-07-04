# Extract text following double-# for targets, as their description for
# the `help` target.	Otherwise These simple-substitutions are resolved
# at reference-time (due to `=` and not `=:`).

# Regex to match targets.
_HelpTargetsCommandRegex = '^[[:print:]]+:.*?\#\# .*$$'
# Source from both Makefile and .mk files.
_HelpTargetsCommand = \
	grep -E ${_HelpTargetsCommandRegex} $(MAKEFILE_LIST) \
		| sed -e 's,^\(Makefile\|.*.mk\):,,'
_HelpTargetsLen	= $(shell ${_HelpTargetsCommand}| cut -d : -f 1| wc -L)
# Printf formats.
_HelpHeaderFormat    = "\033[35m%-${_HelpTargetsLen}s\033[0m \033[32m%-50s\033[0m %s\n"
_HelpHeaderSepFormat = "%-${_HelpTargetsLen}s %-50s %s\n"
_HelpTargetsFormat   = "\033[36m%-${_HelpTargetsLen}s\033[0m %-50s\033[0m %s\n"


.PHONY: help
help: ## Display this screen. //misc
	@printf ${_HelpHeaderFormat}    "Target:" "Description:" "Category:"
	@printf ${_HelpHeaderSepFormat} "-------" "------------" "---------"
	@${_HelpTargetsCommand} \
		| sort \
		| awk 'BEGIN {FS = "(:(.*)?## )|( //)"}; {printf ${_HelpTargetsFormat}, $$1, $$2, $$3}' \
		| awk '{print $$NF,$$0}' | sort | cut -f2- -d' '


_DumpHeaderVarFormat   = "\033[35m%-15s\033[0m \033[32m%s\033[0m\n"
_DumpVarRegex = "^\#|^--|_VAR|_HLP"
_DumpVarComand = \
	make -pn | grep -E -A1 '^\# makefile'| grep -E -v ${_DumpVarRegex}| sort| uniq
_DumpHeaderVarSepFormat = "%-15s %s\n"
_DumpVarFormat          = "\033[36m%-15s\033[0m %s\033[0m\n"

.PHONY: dump
dump: ## Dump Makefile' variables values. //misc
	@printf ${_DumpHeaderVarFormat} "Variable:" "Default value:"
	@printf ${_DumpHeaderVarSepFormat} "--------------" "--------------------"
	@${_DumpVarComand} | awk 'BEGIN {FS = "(:)?= "}; {printf ${_DumpVarFormat}, $$1, $$2}'
