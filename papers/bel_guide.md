# BEL (Biological Expression Language) Quickstart & Guide

Below is a concise, reader-friendly introduction to the **Biological Expression Language (BEL)**. This guide is intended for researchers who already have a strong background in molecular biology but want a straightforward reference for reading or reviewing BEL statements produced by automated pipelines (e.g., from an LLM).

## **Quickstart**

### **1. What is BEL?**

BEL is a language designed to capture biological and biomedical knowledge as structured statements. Each statement connects biological entities (genes, proteins, small molecules) or processes (pathways, phenotypes) with relationships (e.g., increases, decreases, correlates) in a consistent, machine-readable format.

### **2. Basic Syntax**

A BEL **Statement** typically looks like this:

```python
[Subject] [Relationship] [Object]
```

Where **Subject** and **Object** are **BEL Terms**, and **Relationship** is how they interact (e.g., `increases`, `decreases`, `association`). For example:

```python
p(HGNC:TP53) increases bp(GO:"apoptotic process")
```

Meaning: The protein `TP53` **increases** the biological process **apoptotic process**.

### **3. Most Common BEL Functions**

- **p(ns:gene)** — **proteinAbundance**  
  Represents the abundance of a specific protein (e.g., `p(HGNC:TP53)`).

- **g(ns:gene)** — **geneAbundance**  
  Represents the abundance of a gene (e.g., `g(HGNC:CDKN1A)`).

- **r(ns:gene)** — **rnaAbundance**  
  Represents the abundance of RNA (e.g., `r(HGNC:MYC)`).

- **bp(ns:term)** — **biologicalProcess**  
  Represents a biological process (e.g., `bp(GO:"apoptotic process")`).

- **a(ns:chemical)** — **abundance**  
  For small molecules or chemical entities (e.g., `a(CHEBI:"calcium(2+)")`).

### **4. Common Relationships**

- **increases** (`->`)  
- **decreases** (`-|`)  
- **directlyIncreases** (`=>`)  
- **directlyDecreases** (`=|`)  
- **association**  
- **positiveCorrelation** (`pos`)  
- **negativeCorrelation** (`neg`)  

Example:

```python
p(HGNC:AKT1) -> bp(GO:"cell proliferation")
```

Reads as: Protein AKT1 **indirectly increases** cell proliferation.

### **5. A Quick Example**

- text: "Overexpression of p53 can trigger apoptosis in human cell lines.

- "bel_statement": [
  {
    "statement": "p(HGNC:TP53) increases bp(GO:\"apoptotic process\")","evidence":  "Overexpression of p53 can trigger apoptosis in human cell lines."
  }
]

**Interpretation:** The **TP53** protein (when overexpressed) **increases** the biological process **apoptosis**.

---

## **Detailed Discussion**

### **1. BEL Terms & Namespaces**

**BEL Terms** are the core building blocks of statements. Each term is constructed with a **function** (e.g., proteinAbundance) and an **argument** that references a biological entity in a **namespace**. For example:

- **`p(HGNC:EGFR)`**: A protein term for the epidermal growth factor receptor gene, annotated using the HGNC namespace.
- **`bp(GO:"cell cycle arrest")`**: A biological process term for cell cycle arrest, referencing the GO namespace.

**Namespaces** specify how we identify an entity:

- **HGNC** for human gene symbols (e.g., HGNC:TP53)
- **UniProt** for proteins in human or model organisms
- **ChEBI** for small molecules (e.g., CHEBI:glucose)
- **GO** for biological processes or molecular functions (e.g., GO:"cell proliferation")
- **MeSH** for general concepts (diseases, chemicals, etc.)

### **2. BEL Functions**

Below are some common BEL functions (short forms shown in parentheses):

1. **Gene** — `geneAbundance()` → `g(HGNC:CDKN1A)`
2. **RNA** — `rnaAbundance()` → `r(HGNC:MYC)`
3. **Protein** — `proteinAbundance()` → `p(HGNC:EGFR)`
4. **Abundance** — `abundance()` → `a(CHEBI:"lipid A")`
5. **Biological Process** — `biologicalProcess()` → `bp(GO:"apoptotic process")`
6. **Complex** — `complexAbundance()` → `complex(p(HGNC:FOS), p(HGNC:JUN))`
7. **Activity** — `activity()` → `act(p(HGNC:AKT1))`  
   You can optionally specify a molecular activity, e.g. `act(p(HGNC:AKT1), ma(GO:"kinase activity"))`.
8. **Pathology** — `pathology()` → `path(MESH:"Breast Neoplasms")`
9. **Translocation** — `translocation()` → `tloc(p(HGNC:EGFR), fromLoc(GO:"cell surface"), toLoc(GO:endosome))`
10. **Protein Modification** — `proteinModification()` → `pmod(Ph, Ser, 473)` for phosphorylation at Serine 473

**Example**:  

```python
p(HGNC:AKT1, pmod(Ph, Thr, 308), pmod(Ph, Ser, 473))
```

represents the AKT1 protein, phosphorylated at Threonine 308 and Serine 473.

### **3. BEL Relationships**

**Relationships** connect two BEL Terms:

| Relationship         | BEL Notation | Meaning                                     |
|----------------------|--------------|---------------------------------------------|
| increases            | `->`         | A indirectly increases B                    |
| directlyIncreases    | `=>`         | A directly increases B                      |
| decreases            | `-|`         | A indirectly decreases B                    |
| directlyDecreases    | `=|`         | A directly decreases B                      |
| association          | (none/`association`) | A is associated with B               |
| positiveCorrelation  | `pos`        | A is positively correlated with B           |
| negativeCorrelation  | `neg`        | A is negatively correlated with B           |
| regulates            | `reg`        | A regulates B in an unspecified manner      |
| transcribedTo        | `:>`         | gene is transcribed to RNA                  |
| translatedTo         | `>>`         | RNA is translated to protein                |

**Example**:

```python
p(HGNC:TP53) =| p(HGNC:MDM2)
```

Interpreted as: **TP53** directly decreases the abundance of **MDM2**.

### **4. Putting It All Together: Example Statements**

**Example 1:**

```python
p(HGNC:MYC) increases bp(GO:"cell proliferation")
```

- Subject: `p(HGNC:MYC)` (the MYC protein)
- Relationship: `increases` (->)
- Object: `bp(GO:"cell proliferation")` (biological process for cell proliferation)

**Example 2:**

```python
a(CHEBI:"nicotine") -> p(HGNC:CYP1A2)
```

- Nicotine indirectly increases the protein CYP1A2 (implying some regulatory or indirect effect).

**Example 3:**

```python
path(MESH:"Breast Neoplasms") positiveCorrelation bp(GO:"cell cycle arrest")
```

- Breast neoplasm is positively correlated with cell cycle arrest (observational/correlational finding).

### **5. When Reviewing LLM-Generated BEL Statements**

- **Check** that each entity is mapped to the correct namespace (e.g., HGNC, UniProt, GO, etc.).
- **Confirm** that relationships (e.g., `increases`, `decreases`) accurately match the described biological interaction.
- **Ensure** that any modifications (phosphorylation, etc.) or locations (cytoplasm vs. nucleus) are properly captured if mentioned in text.
- **Evaluate** whether the statements match the original text’s context—only capturing interactions explicitly stated or strongly implied.

---

## **Additional Examples**

1. **Simple Increase in a Biological Process**

   ```python
   "text": "Upon DNA damage, p53 triggers apoptosis in the nucleus."
   "bel_statements": [
     {
       "statement": "p(HGNC:TP53) => bp(GO:\"apoptotic process\")",
       "evidence":  "Upon DNA damage, p53 triggers apoptosis in the nucleus."
     }
   ]
   ```

   Interpretation: The p53 protein **directly increases** the apoptosis process.

2. **Protein Complex Formation**

   ```python
   complex(p(HGNC:FOS), p(HGNC:JUN)) => p(HGNC:CDKN1A)
   ```

   The FOS–JUN complex directly increases the abundance (or expression) of CDKN1A (p21).

3. **Positive Correlation vs. Mechanistic Increase**
   - Use **`->`** if mechanistic or functional causation is implied.
   - Use **`pos`** (positiveCorrelation) if only an association is observed, with no direct/indirect mechanistic link in the text.

---

## **Key Takeaways**

- **BEL** statements are structured as **(Term) (Relationship) (Term)**.
- **BEL Terms** always use a **function** like `p()`, `g()`, or `bp()` plus a namespace and identifier.
- **Relationships** capture how two biological entities or processes influence each other (causal, correlative, or otherwise).
- In automated (LLM-generated) BEL, always verify the statements align with the original text’s meaning.
