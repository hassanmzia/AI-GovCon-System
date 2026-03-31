"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  FileText,
  Plus,
  Trash2,
  Eye,
  Download,
  Copy,
  Star,
  Upload,
  Search,
  Filter,
  X,
  Loader2,
  FileType,
  Tag,
  Clock,
  BarChart3,
  CheckCircle2,
  ChevronDown,
  Pencil,
} from "lucide-react";
import {
  getTemplates,
  deleteTemplate,
  createTemplate,
  updateTemplate,
  setDefaultTemplate,
  duplicateTemplate,
  trackDownload,
  renderTemplate,
} from "@/services/templates";
import {
  DocumentTemplate,
  TemplateCategory,
  TemplateFormat,
  CATEGORY_LABELS,
  FORMAT_LABELS,
  TemplateVariable,
} from "@/types/template";

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatFileSize(bytes: number): string {
  if (!bytes) return "--";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const CATEGORY_COLORS: Record<TemplateCategory, string> = {
  proposal: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  capability_statement:
    "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
  past_performance:
    "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  email:
    "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
  contract:
    "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  checklist:
    "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
  pitch_deck:
    "bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300",
  guide:
    "bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300",
  other: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
};

const FORMAT_ICONS: Record<TemplateFormat, string> = {
  docx: "W",
  pdf: "P",
  pptx: "S",
  xlsx: "X",
  txt: "T",
};

// ── Main Component ───────────────────────────────────────────────────────────

export default function TemplateLibraryPage() {
  const [templates, setTemplates] = useState<DocumentTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<TemplateCategory | "">("");
  const [showUpload, setShowUpload] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<DocumentTemplate | null>(null);
  const [showRender, setShowRender] = useState(false);
  const [renderVars, setRenderVars] = useState<Record<string, string>>({});
  const [rendering, setRendering] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Upload form state
  const [uploadName, setUploadName] = useState("");
  const [uploadDesc, setUploadDesc] = useState("");
  const [uploadCategory, setUploadCategory] = useState<TemplateCategory>("proposal");
  const [uploadFormat, setUploadFormat] = useState<TemplateFormat>("docx");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadSource, setUploadSource] = useState("");
  const [uploadTags, setUploadTags] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadTemplates = useCallback(async () => {
    try {
      setLoading(true);
      const params: Record<string, string> = {};
      if (categoryFilter) params.category = categoryFilter;
      if (search) params.search = search;
      const data = await getTemplates(params);
      setTemplates(data.results || []);
    } catch (err) {
      console.error("Failed to load templates:", err);
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, search]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const handleUpload = async () => {
    if (!uploadName) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("name", uploadName);
      formData.append("description", uploadDesc);
      formData.append("category", uploadCategory);
      formData.append("file_format", uploadFormat);
      formData.append("source", uploadSource || "Custom");
      if (uploadTags) {
        formData.append("tags", JSON.stringify(uploadTags.split(",").map((t) => t.trim())));
      }
      if (uploadFile) {
        formData.append("file", uploadFile);
      }
      await createTemplate(formData);
      setShowUpload(false);
      resetUploadForm();
      loadTemplates();
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
    }
  };

  const resetUploadForm = () => {
    setUploadName("");
    setUploadDesc("");
    setUploadCategory("proposal");
    setUploadFormat("docx");
    setUploadFile(null);
    setUploadSource("");
    setUploadTags("");
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this template?")) return;
    setDeleting(id);
    try {
      await deleteTemplate(id);
      loadTemplates();
    } catch (err) {
      console.error("Delete failed:", err);
    } finally {
      setDeleting(null);
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await setDefaultTemplate(id);
      loadTemplates();
    } catch (err) {
      console.error("Set default failed:", err);
    }
  };

  const handleDuplicate = async (id: string) => {
    try {
      await duplicateTemplate(id);
      loadTemplates();
    } catch (err) {
      console.error("Duplicate failed:", err);
    }
  };

  const handleDownload = async (tmpl: DocumentTemplate) => {
    if (!tmpl.file_url) return;
    await trackDownload(tmpl.id);
    window.open(tmpl.file_url, "_blank");
  };

  const openRenderModal = (tmpl: DocumentTemplate) => {
    setSelectedTemplate(tmpl);
    const initial: Record<string, string> = {};
    (tmpl.variables || []).forEach((v) => {
      initial[v.name] = v.default || "";
    });
    setRenderVars(initial);
    setShowRender(true);
  };

  const handleRender = async () => {
    if (!selectedTemplate) return;
    setRendering(true);
    try {
      const blob = await renderTemplate(selectedTemplate.id, renderVars);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rendered_${selectedTemplate.name.replace(/\s+/g, "_").slice(0, 50)}.docx`;
      a.click();
      URL.revokeObjectURL(url);
      setShowRender(false);
    } catch (err) {
      console.error("Render failed:", err);
      alert("Template rendering failed. Make sure the template is a DOCX file with {{variables}}.");
    } finally {
      setRendering(false);
    }
  };

  // Category stats
  const categoryCounts: Record<string, number> = {};
  templates.forEach((t) => {
    categoryCounts[t.category] = (categoryCounts[t.category] || 0) + 1;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Template Library
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Unified document templates — proposals, capability statements, contracts, and more.
            Includes Bidvantage reference templates.
          </p>
        </div>
        <Button onClick={() => setShowUpload(true)} className="gap-2">
          <Upload className="h-4 w-4" />
          Upload Template
        </Button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
        {Object.entries(CATEGORY_LABELS).map(([key, label]) => {
          const count = categoryCounts[key] || 0;
          if (!count && !categoryFilter) return null;
          return (
            <button
              key={key}
              onClick={() =>
                setCategoryFilter(
                  categoryFilter === key ? "" : (key as TemplateCategory)
                )
              }
              className={`rounded-lg px-3 py-2 text-left text-xs transition-all ${
                categoryFilter === key
                  ? "ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/20"
                  : "bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
              } border border-gray-200 dark:border-gray-700`}
            >
              <div className="font-semibold text-gray-900 dark:text-white">
                {count}
              </div>
              <div className="text-gray-500 dark:text-gray-400 truncate">
                {label}
              </div>
            </button>
          );
        })}
      </div>

      {/* Search & Filter */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search templates..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) =>
            setCategoryFilter(e.target.value as TemplateCategory | "")
          }
          className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
        >
          <option value="">All Categories</option>
          {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
        {(categoryFilter || search) && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setCategoryFilter("");
              setSearch("");
            }}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Template Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : templates.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
            <p className="text-gray-500 dark:text-gray-400">
              No templates found. Upload your first template to get started.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {templates.map((tmpl) => (
            <Card
              key={tmpl.id}
              className="hover:shadow-md transition-shadow cursor-pointer group"
            >
              <CardContent className="p-4">
                {/* Header row */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2 min-w-0">
                    {/* Format badge */}
                    <div className="flex-shrink-0 h-9 w-9 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-600 dark:text-gray-300">
                      {FORMAT_ICONS[tmpl.file_format] || "?"}
                    </div>
                    <div className="min-w-0">
                      <h3 className="font-semibold text-sm text-gray-900 dark:text-white truncate">
                        {tmpl.name}
                      </h3>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${
                            CATEGORY_COLORS[tmpl.category] || CATEGORY_COLORS.other
                          }`}
                        >
                          {CATEGORY_LABELS[tmpl.category] || tmpl.category}
                        </span>
                        {tmpl.is_default && (
                          <span className="flex items-center gap-0.5 text-[10px] text-yellow-600 dark:text-yellow-400">
                            <Star className="h-3 w-3 fill-current" />
                            Default
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Description */}
                <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mb-3">
                  {tmpl.description || "No description"}
                </p>

                {/* Meta row */}
                <div className="flex items-center gap-3 text-[10px] text-gray-400 dark:text-gray-500 mb-3">
                  {tmpl.source && (
                    <span className="flex items-center gap-1">
                      <Tag className="h-3 w-3" />
                      {tmpl.source}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <FileType className="h-3 w-3" />
                    {FORMAT_LABELS[tmpl.file_format]}
                  </span>
                  {tmpl.file_size > 0 && (
                    <span>{formatFileSize(tmpl.file_size)}</span>
                  )}
                  <span className="flex items-center gap-1">
                    <BarChart3 className="h-3 w-3" />
                    {tmpl.usage_count} uses
                  </span>
                </div>

                {/* Tags */}
                {tmpl.tags && tmpl.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {tmpl.tags.slice(0, 4).map((tag) => (
                      <span
                        key={tag}
                        className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-[10px] text-gray-600 dark:text-gray-400"
                      >
                        {tag}
                      </span>
                    ))}
                    {tmpl.tags.length > 4 && (
                      <span className="text-[10px] text-gray-400">
                        +{tmpl.tags.length - 4}
                      </span>
                    )}
                  </div>
                )}

                {/* Variables indicator */}
                {tmpl.variables && tmpl.variables.length > 0 && (
                  <div className="text-[10px] text-blue-500 dark:text-blue-400 mb-3">
                    {tmpl.variables.length} template variable
                    {tmpl.variables.length !== 1 ? "s" : ""} — renderable
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-1.5 pt-2 border-t border-gray-100 dark:border-gray-700">
                  {tmpl.file_url && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => handleDownload(tmpl)}
                    >
                      <Download className="h-3 w-3 mr-1" />
                      Download
                    </Button>
                  )}
                  {tmpl.variables &&
                    tmpl.variables.length > 0 &&
                    tmpl.file_format === "docx" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-xs text-blue-600 dark:text-blue-400"
                        onClick={() => openRenderModal(tmpl)}
                      >
                        <Pencil className="h-3 w-3 mr-1" />
                        Fill & Render
                      </Button>
                    )}
                  <div className="flex-1" />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => handleDuplicate(tmpl.id)}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                  {!tmpl.is_default && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => handleSetDefault(tmpl.id)}
                      title="Set as default"
                    >
                      <Star className="h-3 w-3" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-xs text-red-500"
                    onClick={() => handleDelete(tmpl.id)}
                    disabled={deleting === tmpl.id}
                  >
                    {deleting === tmpl.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Trash2 className="h-3 w-3" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* ── Upload Modal ─────────────────────────────────────────────────── */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Upload Template
              </h2>
              <button
                onClick={() => {
                  setShowUpload(false);
                  resetUploadForm();
                }}
              >
                <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Template Name *
                </label>
                <Input
                  value={uploadName}
                  onChange={(e) => setUploadName(e.target.value)}
                  placeholder="e.g. Technical Proposal Template"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={uploadDesc}
                  onChange={(e) => setUploadDesc(e.target.value)}
                  placeholder="Brief description of when to use this template..."
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Category
                  </label>
                  <select
                    value={uploadCategory}
                    onChange={(e) =>
                      setUploadCategory(e.target.value as TemplateCategory)
                    }
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                  >
                    {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Format
                  </label>
                  <select
                    value={uploadFormat}
                    onChange={(e) =>
                      setUploadFormat(e.target.value as TemplateFormat)
                    }
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                  >
                    {Object.entries(FORMAT_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Source
                  </label>
                  <Input
                    value={uploadSource}
                    onChange={(e) => setUploadSource(e.target.value)}
                    placeholder="e.g. Bidvantage, Custom"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tags (comma-separated)
                  </label>
                  <Input
                    value={uploadTags}
                    onChange={(e) => setUploadTags(e.target.value)}
                    placeholder="proposal, rfp, federal"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Template File
                </label>
                <div
                  className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {uploadFile ? (
                    <div className="flex items-center justify-center gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        {uploadFile.name} ({formatFileSize(uploadFile.size)})
                      </span>
                    </div>
                  ) : (
                    <div>
                      <Upload className="h-8 w-8 mx-auto text-gray-400 mb-2" />
                      <p className="text-sm text-gray-500">
                        Click to select a file (DOCX, PDF, PPTX, XLSX)
                      </p>
                    </div>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept=".docx,.pdf,.pptx,.xlsx,.txt"
                    onChange={(e) =>
                      setUploadFile(e.target.files?.[0] || null)
                    }
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowUpload(false);
                    resetUploadForm();
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleUpload}
                  disabled={!uploadName || uploading}
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Render Modal ─────────────────────────────────────────────────── */}
      {showRender && selectedTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg mx-4 p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Fill & Render Template
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  {selectedTemplate.name}
                </p>
              </div>
              <button onClick={() => setShowRender(false)}>
                <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              </button>
            </div>

            <div className="space-y-3">
              {selectedTemplate.variables &&
              selectedTemplate.variables.length > 0 ? (
                selectedTemplate.variables.map((v) => (
                  <div key={v.name}>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      {v.label}
                    </label>
                    <Input
                      value={renderVars[v.name] || ""}
                      onChange={(e) =>
                        setRenderVars((prev) => ({
                          ...prev,
                          [v.name]: e.target.value,
                        }))
                      }
                      placeholder={v.default || v.label}
                    />
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">
                  No variables defined. The template will be downloaded as-is.
                </p>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-4 mt-4 border-t border-gray-200 dark:border-gray-700">
              <Button variant="outline" onClick={() => setShowRender(false)}>
                Cancel
              </Button>
              <Button onClick={handleRender} disabled={rendering}>
                {rendering ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Rendering...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Render & Download
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
