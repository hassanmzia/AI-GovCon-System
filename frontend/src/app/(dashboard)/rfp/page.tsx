"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getRFPDocuments,
  getComplianceMatrix,
  createRFPDocument,
} from "@/services/rfp";
import {
  RFPDocument,
  ComplianceMatrixItem,
  DocumentType,
  ExtractionStatus,
  ComplianceStatus,
} from "@/types/rfp";
import { fetchAllDeals } from "@/services/analytics";
import { Deal } from "@/types/deal";
import {
  Search,
  Loader2,
  Upload,
  FileText,
  X,
  CheckCircle2,
  AlertCircle,
  Clock,
  MinusCircle,
} from "lucide-react";

const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  rfp: "RFP",
  rfi: "RFI",
  rfq: "RFQ",
  sources_sought: "Sources Sought",
  amendment: "Amendment",
  qa_response: "Q&A Response",
  attachment: "Attachment",
  other: "Other",
};

const EXTRACTION_STATUS_CLASSES: Record<ExtractionStatus, string> = {
  pending: "bg-gray-100 text-gray-600",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

const EXTRACTION_STATUS_LABELS: Record<ExtractionStatus, string> = {
  pending: "Pending",
  processing: "Processing",
  completed: "Parsed",
  failed: "Failed",
};

const COMPLIANCE_STATUS_CLASSES: Record<ComplianceStatus, string> = {
  compliant: "bg-green-100 text-green-700",
  partial: "bg-yellow-100 text-yellow-700",
  non_compliant: "bg-red-100 text-red-700",
  not_assessed: "bg-gray-100 text-gray-600",
};

const COMPLIANCE_STATUS_LABELS: Record<ComplianceStatus, string> = {
  compliant: "Compliant",
  partial: "Partial",
  non_compliant: "Non-Compliant",
  not_assessed: "Not Assessed",
};

const RESPONSE_STATUS_LABELS: Record<string, string> = {
  not_started: "Not Started",
  in_progress: "In Progress",
  drafted: "Drafted",
  reviewed: "Reviewed",
  final: "Final",
};

function ParsingStatusBadge({ status }: { status: ExtractionStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${EXTRACTION_STATUS_CLASSES[status] || "bg-gray-100 text-gray-600"}`}
    >
      {EXTRACTION_STATUS_LABELS[status] || status}
    </span>
  );
}

function ComplianceStatusBadge({ status }: { status: ComplianceStatus }) {
  const icons: Record<ComplianceStatus, React.ReactNode> = {
    compliant: <CheckCircle2 className="h-3 w-3" />,
    partial: <AlertCircle className="h-3 w-3" />,
    non_compliant: <MinusCircle className="h-3 w-3" />,
    not_assessed: <Clock className="h-3 w-3" />,
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${COMPLIANCE_STATUS_CLASSES[status] || "bg-gray-100 text-gray-600"}`}
    >
      {icons[status]}
      {COMPLIANCE_STATUS_LABELS[status] || status}
    </span>
  );
}

interface ComplianceMatrixPanelProps {
  document: RFPDocument;
  onClose: () => void;
}

function ComplianceMatrixPanel({
  document,
  onClose,
}: ComplianceMatrixPanelProps) {
  const [items, setItems] = useState<ComplianceMatrixItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMatrix = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getComplianceMatrix(document.id);
        setItems(data.results || []);
      } catch {
        setError("Failed to load compliance matrix.");
      } finally {
        setLoading(false);
      }
    };
    fetchMatrix();
  }, [document.id]);

  // Summary metrics
  const totalItems = items.length;
  const compliantCount = items.filter(
    (i) => i.compliance_status === "compliant"
  ).length;
  const notStartedCount = items.filter(
    (i) => i.response_status === "not_started"
  ).length;
  const compliantPct =
    totalItems > 0 ? Math.round((compliantCount / totalItems) * 100) : 0;

  const truncate = (str: string, maxLen: number) => {
    if (!str) return "--";
    return str.length > maxLen ? str.slice(0, maxLen) + "..." : str;
  };

  return (
    <div className="space-y-4">
      {/* Panel header */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base font-semibold">
                Compliance Matrix
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-0.5 truncate">
                {document.title}
              </p>
            </div>
            <button
              onClick={onClose}
              className="ml-3 rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Close compliance matrix"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </CardHeader>
        {!loading && !error && totalItems > 0 && (
          <CardContent className="pt-0">
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg border bg-muted/30 p-3 text-center">
                <p className="text-2xl font-bold tabular-nums">{totalItems}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Total Requirements
                </p>
              </div>
              <div className="rounded-lg border bg-green-50 p-3 text-center">
                <p className="text-2xl font-bold tabular-nums text-green-700">
                  {compliantPct}%
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Compliant
                </p>
              </div>
              <div className="rounded-lg border bg-yellow-50 p-3 text-center">
                <p className="text-2xl font-bold tabular-nums text-yellow-700">
                  {notStartedCount}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Not Started
                </p>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Matrix table */}
      <Card>
        <CardContent className="pt-4">
          {loading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-3 text-sm text-muted-foreground">
                Loading compliance matrix...
              </span>
            </div>
          ) : error ? (
            <div className="py-10 text-center">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10">
              <FileText className="h-10 w-10 text-muted-foreground opacity-40 mb-2" />
              <p className="text-sm text-muted-foreground">
                No compliance matrix items yet.
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Parse the document to generate compliance matrix items.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-3 pr-3 font-medium text-muted-foreground whitespace-nowrap">
                      Req ID
                    </th>
                    <th className="pb-3 pr-3 font-medium text-muted-foreground">
                      Requirement
                    </th>
                    <th className="pb-3 pr-3 font-medium text-muted-foreground whitespace-nowrap">
                      Type
                    </th>
                    <th className="pb-3 pr-3 font-medium text-muted-foreground whitespace-nowrap">
                      Compliance
                    </th>
                    <th className="pb-3 pr-3 font-medium text-muted-foreground whitespace-nowrap">
                      Owner
                    </th>
                    <th className="pb-3 font-medium text-muted-foreground whitespace-nowrap">
                      Response
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr
                      key={item.id}
                      className="border-b hover:bg-muted/40 transition-colors"
                    >
                      <td className="py-3 pr-3 font-mono text-xs text-muted-foreground whitespace-nowrap">
                        {item.requirement_id || "--"}
                      </td>
                      <td className="py-3 pr-3 max-w-[240px]">
                        <span
                          title={item.requirement_text}
                          className="text-muted-foreground"
                        >
                          {truncate(item.requirement_text || "", 80)}
                        </span>
                      </td>
                      <td className="py-3 pr-3 whitespace-nowrap">
                        {item.requirement_type ? (
                          <span className="text-xs capitalize text-muted-foreground">
                            {item.requirement_type}
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            --
                          </span>
                        )}
                      </td>
                      <td className="py-3 pr-3 whitespace-nowrap">
                        <ComplianceStatusBadge
                          status={item.compliance_status}
                        />
                      </td>
                      <td className="py-3 pr-3 whitespace-nowrap">
                        {item.response_owner_name ? (
                          <span className="text-xs">{item.response_owner_name}</span>
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            Unassigned
                          </span>
                        )}
                      </td>
                      <td className="py-3 whitespace-nowrap">
                        <span className="text-xs text-muted-foreground">
                          {RESPONSE_STATUS_LABELS[item.response_status] ||
                            item.response_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ── Upload RFP Modal ──────────────────────────────────────────────────────

interface UploadRFPModalProps {
  onClose: () => void;
  onCreated: (doc: RFPDocument) => void;
}

function UploadRFPModal({ onClose, onCreated }: UploadRFPModalProps) {
  const [title, setTitle] = useState("");
  const [dealId, setDealId] = useState("");
  const [documentType, setDocumentType] = useState<DocumentType>("rfp");
  const [fileUrl, setFileUrl] = useState("");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [dealsLoading, setDealsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allDocTypes: DocumentType[] = [
    "rfp", "rfi", "rfq", "sources_sought",
    "amendment", "qa_response", "attachment", "other",
  ];

  useEffect(() => {
    fetchAllDeals()
      .then((d) => setDeals(d))
      .catch(() => {})
      .finally(() => setDealsLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !dealId) {
      setError("Title and deal are required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const doc = await createRFPDocument({
        title: title.trim(),
        deal: dealId,
        document_type: documentType,
        file_url: fileUrl.trim() || undefined,
      });
      onCreated(doc);
    } catch {
      setError("Failed to upload RFP document. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-background shadow-lg">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">Upload RFP Document</h2>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">
              Document Title <span className="text-red-500">*</span>
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Solicitation No. FA8650-24-R-0001"
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">
              Deal <span className="text-red-500">*</span>
            </label>
            {dealsLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading deals...
              </div>
            ) : (
              <select
                value={dealId}
                onChange={(e) => setDealId(e.target.value)}
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">Select a deal...</option>
                {deals.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.title}
                  </option>
                ))}
              </select>
            )}
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Document Type</label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value as DocumentType)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              {allDocTypes.map((t) => (
                <option key={t} value={t}>
                  {DOCUMENT_TYPE_LABELS[t]}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">File URL (optional)</label>
            <Input
              value={fileUrl}
              onChange={(e) => setFileUrl(e.target.value)}
              placeholder="https://sam.gov/opp/..."
              type="url"
            />
            <p className="text-xs text-muted-foreground">
              Link to the document on SAM.gov or your file storage.
            </p>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting || dealsLoading}>
              {submitting ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Uploading...</>
              ) : (
                <><Upload className="mr-2 h-4 w-4" />Upload</>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

export default function RFPPage() {
  const [documents, setDocuments] = useState<RFPDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<RFPDocument | null>(
    null
  );

  const [showUploadModal, setShowUploadModal] = useState(false);

  // Filters
  const [search, setSearch] = useState("");
  const [docTypeFilter, setDocTypeFilter] = useState("");

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (docTypeFilter) params.document_type = docTypeFilter;

      const data = await getRFPDocuments(params);
      setDocuments(data.results || []);
    } catch {
      setError("Failed to load RFP documents. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [search, docTypeFilter]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleRowClick = (doc: RFPDocument) => {
    setSelectedDocument((prev) => (prev?.id === doc.id ? null : doc));
  };

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return "--";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const truncate = (str: string, maxLen: number) => {
    if (!str) return "--";
    return str.length > maxLen ? str.slice(0, maxLen) + "..." : str;
  };

  const allDocTypes: DocumentType[] = [
    "rfp",
    "rfi",
    "rfq",
    "sources_sought",
    "amendment",
    "qa_response",
    "attachment",
    "other",
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">RFP Workspace</h1>
          <p className="text-muted-foreground">
            Upload, parse, and track RFP documents and compliance requirements
          </p>
        </div>
        <Button onClick={() => setShowUploadModal(true)}>
          <Upload className="mr-2 h-4 w-4" />
          Upload RFP
        </Button>
      </div>

      {showUploadModal && (
        <UploadRFPModal
          onClose={() => setShowUploadModal(false)}
          onCreated={(doc) => {
            setDocuments((prev) => [doc, ...prev]);
            setShowUploadModal(false);
          }}
        />
      )}

      {/* Filter Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative w-full sm:flex-1 sm:min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search RFP documents..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <select
              value={docTypeFilter}
              onChange={(e) => setDocTypeFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Document Types</option>
              {allDocTypes.map((t) => (
                <option key={t} value={t}>
                  {DOCUMENT_TYPE_LABELS[t]}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Main content: list + optional compliance matrix */}
      <div className="space-y-6">
        {/* Documents List */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              RFP Documents
              {!loading && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  ({documents.length} results)
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-3 text-muted-foreground">
                  Loading documents...
                </span>
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center py-12">
                <p className="text-red-600 mb-4">{error}</p>
                <Button variant="outline" onClick={fetchDocuments}>
                  Retry
                </Button>
              </div>
            ) : documents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground mb-3 opacity-50" />
                <p className="text-muted-foreground font-medium">
                  No RFP documents found
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {search || docTypeFilter
                    ? "Try adjusting your filters."
                    : "Upload your first RFP document to get started."}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Title
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Deal
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Type
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Amendment
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Status
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Parsing
                      </th>
                      <th className="pb-3 font-medium text-muted-foreground">
                        Uploaded
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((doc) => {
                      const isSelected = selectedDocument?.id === doc.id;
                      const parsingStatus =
                        (doc.parsing_status as ExtractionStatus) ||
                        doc.extraction_status;
                      return (
                        <tr
                          key={doc.id}
                          onClick={() => handleRowClick(doc)}
                          className={`border-b cursor-pointer transition-colors hover:bg-muted/50 ${
                            isSelected ? "bg-muted/70" : ""
                          }`}
                        >
                          <td className="py-3 pr-4 font-medium">
                            {truncate(doc.title, 45)}
                          </td>
                          <td className="py-3 pr-4">
                            {doc.deal_name ? (
                              <span className="text-primary hover:underline cursor-pointer">
                                {truncate(doc.deal_name, 30)}
                              </span>
                            ) : (
                              <span className="text-muted-foreground text-xs">
                                {doc.deal ? truncate(doc.deal, 20) : "--"}
                              </span>
                            )}
                          </td>
                          <td className="py-3 pr-4">
                            <span className="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-secondary text-secondary-foreground">
                              {DOCUMENT_TYPE_LABELS[doc.document_type] ||
                                doc.document_type}
                            </span>
                          </td>
                          <td className="py-3 pr-4 text-muted-foreground">
                            {doc.amendment_number != null
                              ? `#${doc.amendment_number}`
                              : "--"}
                          </td>
                          <td className="py-3 pr-4 text-muted-foreground text-xs capitalize">
                            {doc.status || "active"}
                          </td>
                          <td className="py-3 pr-4">
                            <ParsingStatusBadge status={parsingStatus} />
                          </td>
                          <td className="py-3 text-muted-foreground">
                            {formatDate(doc.uploaded_at || doc.created_at)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Compliance Matrix Panel */}
        {selectedDocument && (
          <ComplianceMatrixPanel
            document={selectedDocument}
            onClose={() => setSelectedDocument(null)}
          />
        )}
      </div>
    </div>
  );
}
