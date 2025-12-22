include deps/jaywalker-utils/common/makefile/makefile-package

build:  ##@Docker Build clockodo-mcp:latest image
	docker build -t clockodo-mcp:latest .

unittests:  ##@Docker Build docker
