#!/usr/bin/env bash

REGIONS=(eu-central-1 eu-west-1 us-east-1 us-east-2 us-west-1 us-west-2 ca-central-1 ap-southeast-1 ap-southeast-2 sa-east-1)

for REGION in "${REGIONS[@]}"
do
   echo "== ${REGION}"
   aws elb --region $REGION describe-load-balancers | jq -r '.LoadBalancerDescriptions[].LoadBalancerName'
done

