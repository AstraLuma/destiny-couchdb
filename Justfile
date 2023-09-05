help:
  just --list

start-couch:
  docker run --detach --rm --name bungie-couch --volume $PWD/.couch:/opt/couchdb/data -p 5984:5984 -e COUCHDB_USER=admin -e COUCHDB_PASSWORD=admin couchdb

init-couch:
  curl -X PUT http://admin:admin@localhost:5984/_users
  curl -X PUT http://admin:admin@localhost:5984/_replicator
  curl -X PUT http://admin:admin@localhost:5984/_global_changes

fauxton:
  xdg-open http://localhost:5984/_utils/
