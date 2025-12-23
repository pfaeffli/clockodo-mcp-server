include deps/jaywalker-utils/common/makefile/makefile-package

build-mcp:  ##@Docker Build clockodo-mcp:latest image
	docker build -t clockodo-mcp:latest .

unittests:  ##@Docker Build docker
	docker-compose -f docker-compose.test.yml up test

manual-test:  ##@Manual Start Jupyter notebook for manual testing
	docker-compose -f docker-compose.test.yml up jupyter
