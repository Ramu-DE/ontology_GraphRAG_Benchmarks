# Neptune + OpenSearch Connection Information

## Infrastructure Created ✅

**Created:** 2026-05-12  
**Region:** us-west-2  
**Account:** 210999745354  

---

## Neptune Database

**Cluster ID:** graphrag-neptune-cluster  
**Instance ID:** graphrag-neptune-instance  
**Instance Class:** db.t3.medium  
**Engine:** Neptune  
**Port:** 8182  

**Endpoint:**
```
graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182
```

**Connection String:**
```
wss://graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182/gremlin
```

---

## OpenSearch

**Domain:** graphrag-opensearch  
**Instance:** t3.small.search  
**Engine:** OpenSearch 2.11  
**Port:** 443  

**Credentials:**
- Username: `admin`
- Password: `GraphRAG2024!`

**Endpoint:**
```
https://search-graphrag-opensearch-cjs5ycirmg65pqvaj2q3w76oy4.us-west-2.es.amazonaws.com
```

---

## Security

**Security Group:** sg-0b0e2be68851d73bc  
**VPC:** vpc-097a149637cc1b2e5  
**Subnets:** subnet-0611e4c21f24ec7b6, subnet-0511317f09d952d33  

**Ingress Rules:**
- Port 8182 (Neptune) - within security group
- Port 443 (HTTPS) - within security group

---

## Status Monitoring

Check status:
```bash
bash neptune_infrastructure_status.sh
```

Or manually:
```bash
# Neptune
aws neptune describe-db-instances \
    --db-instance-identifier graphrag-neptune-instance \
    --region us-west-2

# OpenSearch
aws opensearch describe-domain \
    --domain-name graphrag-opensearch \
    --region us-west-2
```

---

## Current Status

| Resource | Status | ETA |
|----------|--------|-----|
| Neptune Cluster | ✅ Available | Ready |
| Neptune Instance | ✅ Available | Ready |
| OpenSearch | ✅ Available | Ready |

---

## Cost

**Hourly:**
- Neptune db.t3.medium: $0.082/hr
- OpenSearch t3.small: $0.036/hr
- Storage & transfer: ~$0.01/hr
- **Total: ~$0.13/hr**

**4-hour test:** ~$0.52  
**8-hour test:** ~$1.04  

---

## Next Steps

1. **Wait for provisioning** (~20-30 minutes)
   ```bash
   bash neptune_infrastructure_status.sh
   ```

2. **Load data**
   - Neptune: Gremlin bulk loader
   - OpenSearch: Bulk API with vectors

3. **Run benchmarks**
   - Two-layer queries (OpenSearch → Neptune)
   - Measure friction overhead

4. **Compare results**
   - Neptune two-layer: Expected ~400-500ms
   - Neo4j unified: Measured 195ms
   - Speedup: Expected 2-2.5×

---

## Cleanup

When done testing:
```bash
# Delete Neptune instance
aws neptune delete-db-instance \
    --db-instance-identifier graphrag-neptune-instance \
    --skip-final-snapshot \
    --region us-west-2

# Delete Neptune cluster
aws neptune delete-db-cluster \
    --db-cluster-identifier graphrag-neptune-cluster \
    --skip-final-snapshot \
    --region us-west-2

# Delete OpenSearch
aws opensearch delete-domain \
    --domain-name graphrag-opensearch \
    --region us-west-2

# Delete subnet group (after instances deleted)
aws neptune delete-db-subnet-group \
    --db-subnet-group-name graphrag-subnet-group \
    --region us-west-2

# Delete security group (after all resources deleted)
aws ec2 delete-security-group \
    --group-id sg-0b0e2be68851d73bc \
    --region us-west-2
```

---

## Support Files

- `neptune_infrastructure_status.sh` - Status monitoring
- `NEPTUNE_CONNECTION_INFO.md` - This file
- `neptune_opensearch_benchmark.py` - Benchmark implementation (to be created)
