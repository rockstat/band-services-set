bump-patch:
	bumpversion patch

bump-minor:
	bumpversion minor

to_master:
	sh -c 'git checkout master && git merge dev && git push origin master && git checkout dev'