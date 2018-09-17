# Insurance Data Model

The Insurance Data Model (IDM) is meant to define and implement a standard for insurance relevant data such as policy terms and conditions, information about insured objects, reinsurance, claims, etc. This project has been motivated by the need to have an open and concise description of insurance coverages, in particular, for applications such as reinsurance and probabilistic cat modeling. Additional applications covering the entire insurance life-cycle like pricing, underwriting, claims handling, data enrichment and analysis, and automation have been kept in mind from the very beginning.

## 1. Design principles

The definition and implementation of the IDM is based on the following criteria:

* Preciseness
* Flexibility
* Security
* Interoperability/Accessibility

### 1.1 Preciseness

The IDM should designed in a way that it does not limit the representation of reality. For example, insurance terms and conditions shall be representated in exactly the way they are fomulated in the legally binding policy. At the same time, redundancy shall be avoided. 

### 1.2 Flexibility

The IDM must be easily extendible, in order to account for [1.1] in case of new structures, data, or use cases.

### 1.3 Security

Due to the fact the IDM may hold personal data it is essential to support encryption of data both at rest and on transit and access management on an arbitrary granular level. Additionally, data locality must be supported to allow for additional security meassures.

### 1.4 Interoperability/Accessibility

The constraints on hardware, software, operating system, (cloud) architecures for deploying and or accessing the IDM should be minimal and allow for maximal flexibility.
