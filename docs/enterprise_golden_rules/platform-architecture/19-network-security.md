# Network Security Standards

> **Document Owner:** Security Team | **Status:** Approved | **Last Updated:** February 2026

## Overview

This document defines network security standards for the Databricks platform, covering VNet injection, Private Links, IP access controls, and encryption requirements.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **SEC-01** | Production workspaces must use VNet injection | Critical |
| **SEC-02** | Configure Azure Private Link for control plane access | Critical |
| **SEC-03** | Implement IP access lists for workspace access | Required |
| **SEC-04** | Use customer-managed keys (CMK) for encryption | Required |
| **SEC-05** | Enable diagnostic logging to Azure Monitor | Critical |
| **SEC-06** | Configure network egress controls | Required |
| **SEC-07** | Use secure cluster connectivity (no public IPs) | Critical |

---

## SEC-01: VNet Injection

### Rule
All production workspaces must deploy compute resources into customer-managed VNets.

### Why It Matters
- Full control over network routing and security
- Integration with corporate networking infrastructure
- Eliminates public internet exposure for cluster nodes
- Enables custom firewall rules and traffic inspection

### Implementation

```
Customer VNet
├── public-subnet (NAT gateway)
│   └── Databricks control plane connectivity
├── private-subnet (worker nodes)
│   └── Cluster compute resources
└── Network Security Groups
    └── Ingress/egress rules
```

### Required Subnet Configuration

| Subnet | CIDR (minimum) | Purpose |
|--------|----------------|---------|
| Public | /26 (64 IPs) | Control plane connectivity |
| Private | /26 (64 IPs) | Worker nodes |

### NSG Rules (Minimum)

| Direction | Port | Source/Dest | Purpose |
|-----------|------|-------------|---------|
| Inbound | 443 | Databricks control plane | Secure cluster connectivity |
| Outbound | 443 | Azure services | Metastore, storage, APIs |
| Outbound | 3306 | Azure SQL | Hive metastore (legacy) |

---

## SEC-02: Azure Private Link

### Rule
Configure Private Link endpoints for control plane access to eliminate public internet transit.

### Why It Matters
- All management traffic stays on Azure backbone
- No public IP exposure for workspace access
- Enhanced security for sensitive workloads
- Supports compliance requirements for private connectivity

### Architecture

```
User Network
    │
    └── Private Endpoint (workspace)
            │
            └── Azure Private Link
                    │
                    └── Databricks Control Plane (private)
```

### Implementation

1. **Create Private Endpoint for workspace**
2. **Configure private DNS zone** (`privatelink.azuredatabricks.net`)
3. **Disable public network access** (optional, recommended)
4. **Test connectivity** from corporate network

### Verification
```bash
# Test private endpoint resolution
nslookup myworkspace.azuredatabricks.net
# Should resolve to private IP (10.x.x.x), not public
```

---

## SEC-03: IP Access Lists

### Rule
Configure IP access lists to restrict workspace access to known trusted networks.

### Why It Matters
- Additional security layer beyond authentication
- Prevents access from untrusted networks
- Reduces attack surface
- Supports compliance requirements

### Configuration

```json
{
  "ip_access_lists": [
    {
      "label": "Corporate VPN",
      "list_type": "ALLOW",
      "ip_addresses": ["10.0.0.0/8", "172.16.0.0/12"]
    },
    {
      "label": "Known Threats",
      "list_type": "BLOCK",
      "ip_addresses": ["192.168.100.0/24"]
    }
  ]
}
```

### Environment Policies

| Environment | IP Access Policy |
|-------------|------------------|
| Production | Corporate VPN + known IPs only |
| Staging | Corporate VPN + CI/CD runners |
| Development | Corporate VPN (broader) |

---

## SEC-04: Customer-Managed Keys (CMK)

### Rule
Use customer-managed keys in Azure Key Vault for workspace encryption.

### Why It Matters
- Complete control over encryption key lifecycle
- Supports regulatory compliance (FIPS 140-2)
- Enables key revocation capability
- Provides audit trail for key operations

### Implementation Steps

1. **Create Azure Key Vault** with soft delete and purge protection
2. **Generate or import encryption key** (RSA 2048 minimum)
3. **Configure key rotation policy** (recommended: annual)
4. **Enable CMK for workspace** (during creation or migration)

### Key Vault Requirements

| Setting | Value |
|---------|-------|
| Soft delete | Enabled (required) |
| Purge protection | Enabled (recommended) |
| Key type | RSA 2048 or higher |
| Permissions | Databricks service principal: Get, Wrap, Unwrap |

---

## SEC-05: Diagnostic Logging

### Rule
Enable diagnostic logging to Azure Monitor for all security-relevant events.

### Why It Matters
- Centralized security monitoring
- Enables threat detection and investigation
- Supports compliance audit requirements
- Integrates with SIEM systems

### Required Log Categories

| Category | Description |
|----------|-------------|
| dbfs | DBFS operations |
| clusters | Cluster lifecycle |
| accounts | User/group management |
| jobs | Job execution |
| notebook | Notebook operations |
| workspace | Workspace events |
| unityCatalog | Data governance events |

### Implementation
```bash
# Azure CLI
az monitor diagnostic-settings create \
  --name databricks-logs \
  --resource /subscriptions/.../workspaces/my-workspace \
  --logs '[{"category":"dbfs","enabled":true},...]' \
  --workspace /subscriptions/.../workspaces/log-analytics
```

---

## SEC-06: Network Egress Controls

### Rule
Implement network egress controls to prevent unauthorized data exfiltration.

### Why It Matters
- Prevents unauthorized data transfer
- Provides visibility into data movement
- Supports compliance requirements
- Enables detection of anomalous activity

### Implementation Options

| Option | Use Case |
|--------|----------|
| Azure Firewall | Comprehensive traffic inspection |
| NSG rules | Basic port/IP filtering |
| NAT Gateway | Predictable egress IPs for allowlisting |
| UDRs | Custom routing through security appliances |

### Recommended Egress Rules

```
Allow:
├── Azure Storage (*.blob.core.windows.net)
├── Azure SQL (*.database.windows.net)
├── Databricks services (*.azuredatabricks.net)
├── PyPI/Maven (package managers)
└── Corporate services (specific IPs)

Deny:
└── All other outbound traffic
```

---

## SEC-07: Secure Cluster Connectivity

### Rule
Enable secure cluster connectivity (no public IPs) for all production clusters.

### Why It Matters
- Eliminates public IP addresses on cluster nodes
- All traffic flows through control plane
- Reduces attack surface significantly
- Simplifies network security management

### Verification
```sql
-- Check cluster configuration
SELECT cluster_id, cluster_name, 
       single_user_name,
       data_security_mode
FROM system.compute.clusters
WHERE enable_elastic_disk = true;
```

### Requirements

- VNet injection enabled
- Outbound connectivity to control plane
- Private Link or secure tunnel for management

---

## Security Compliance Add-ons

### Enhanced Security and Compliance

For regulated industries (HIPAA, PCI-DSS, SOC 2):

| Feature | Description |
|---------|-------------|
| Compliance security profile | Industry-specific controls |
| Automatic security updates | Patching without disruption |
| Enhanced monitoring | Additional audit capabilities |
| Image hardening | CIS benchmark compliance |

### When Required

- Healthcare (HIPAA)
- Financial services (PCI-DSS, SOX)
- Government (FedRAMP)
- Any SOC 2 Type II audit scope

---

## Validation Checklist

### Network Architecture
- [ ] VNet injection configured for production
- [ ] Private Link enabled for control plane
- [ ] IP access lists implemented
- [ ] Secure cluster connectivity enabled

### Encryption
- [ ] Customer-managed keys configured
- [ ] Key rotation policy in place
- [ ] Key Vault soft delete enabled

### Monitoring
- [ ] Diagnostic logging to Azure Monitor
- [ ] SIEM integration configured
- [ ] Security alerts defined

### Egress Controls
- [ ] Firewall/NSG rules defined
- [ ] Data exfiltration monitoring enabled
- [ ] Approved egress destinations documented

---

## Quick Reference

```bash
# Check workspace network configuration
az databricks workspace show --name myworkspace -g mygroup \
  --query "{vnet:parameters.customVirtualNetworkId.value, privateLink:privateEndpointConnections}"

# List IP access lists
databricks ip-access-lists list

# Check diagnostic settings
az monitor diagnostic-settings list --resource /subscriptions/.../workspaces/myworkspace
```

---

## Related Documents

- [Platform Overview](10-platform-overview.md)
- [Secrets & Workspace Management](14-secrets-workspace-management.md)
- [Unity Catalog Governance](15-unity-catalog-governance.md)

---

## References

- [Architecture Best Practices for Azure Databricks - Security](https://learn.microsoft.com/en-us/azure/well-architected/service-guides/azure-databricks#security)
- [Azure Databricks Security Baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/azure-databricks-security-baseline)
- [VNet Injection](https://learn.microsoft.com/en-us/azure/databricks/security/network/classic/vnet-inject)
- [Private Link](https://learn.microsoft.com/en-us/azure/databricks/security/network/front-end/front-end-private-connect)
- [IP Access Lists](https://learn.microsoft.com/en-us/azure/databricks/security/network/front-end/ip-access-list)
