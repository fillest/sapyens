CREATE TABLE test
(
  data text NOT NULL
)
WITH (
  OIDS=FALSE
);

INSERT INTO test(
            data)
    VALUES ('1');
