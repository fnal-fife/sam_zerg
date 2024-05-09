#!/bin/bash

oc project samdev; cd samdev; make apply; cd ..;
oc project samannie; cd annie/; make apply; cd ..;
oc project samgm2; cd gm2/; make apply; cd ..;
oc project samminerva; cd minerva/; make apply; cd ..;
oc project samminos; cd minos/; make apply; cd ..;
oc project samsbn; cd sbn/; make apply; cd ..;
oc project samsbnd; cd sbnd/; make apply; cd ..;
oc project samdune; cd dune/; make apply; cd ..;
oc project samlariat; cd lariat/; make apply; cd ..;
