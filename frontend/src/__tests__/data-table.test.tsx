/**
 * Tests for the DataTable reusable component.
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { DataTable, Column } from "@/components/ui/data-table";

// Mock next/navigation and lucide-react icons to avoid ES module issues
jest.mock("lucide-react", () => ({
  ChevronUp: () => <span data-testid="chevron-up" />,
  ChevronDown: () => <span data-testid="chevron-down" />,
  ChevronsUpDown: () => <span data-testid="chevrons-updown" />,
  Search: () => <span data-testid="search-icon" />,
  ChevronLeft: () => <span data-testid="chevron-left" />,
  ChevronRight: () => <span data-testid="chevron-right" />,
}));

// ── Fixtures ─────────────────────────────────────────────────────────────────

interface Row {
  id: string;
  name: string;
  value: number;
}

const columns: Column<Row>[] = [
  { key: "name", header: "Name", sortable: true },
  { key: "value", header: "Value", sortable: true },
];

const data: Row[] = [
  { id: "1", name: "Alice", value: 300 },
  { id: "2", name: "Bob", value: 100 },
  { id: "3", name: "Charlie", value: 200 },
];

const rowKey = (row: Row) => row.id;

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("DataTable", () => {
  it("renders all rows", () => {
    render(<DataTable data={data} columns={columns} rowKey={rowKey} />);
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("Charlie")).toBeInTheDocument();
  });

  it("renders column headers", () => {
    render(<DataTable data={data} columns={columns} rowKey={rowKey} />);
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Value")).toBeInTheDocument();
  });

  it("shows emptyMessage when data is empty", () => {
    render(
      <DataTable
        data={[]}
        columns={columns}
        rowKey={rowKey}
        emptyMessage="Nothing here"
      />
    );
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
  });

  it("filters rows based on search input", () => {
    render(<DataTable data={data} columns={columns} rowKey={rowKey} />);
    const input = screen.getByPlaceholderText("Search...");
    fireEvent.change(input, { target: { value: "alice" } });
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.queryByText("Bob")).not.toBeInTheDocument();
  });

  it("clears filter when search is cleared", () => {
    render(<DataTable data={data} columns={columns} rowKey={rowKey} />);
    const input = screen.getByPlaceholderText("Search...");
    fireEvent.change(input, { target: { value: "alice" } });
    fireEvent.change(input, { target: { value: "" } });
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("Charlie")).toBeInTheDocument();
  });

  it("does not show search when searchable=false", () => {
    render(
      <DataTable data={data} columns={columns} rowKey={rowKey} searchable={false} />
    );
    expect(screen.queryByPlaceholderText("Search...")).not.toBeInTheDocument();
  });

  it("sorts ascending on first header click", () => {
    render(<DataTable data={data} columns={columns} rowKey={rowKey} />);
    const nameHeader = screen.getByText("Name");
    fireEvent.click(nameHeader);
    const rows = screen.getAllByRole("row");
    // rows[0] is thead row, rows[1..3] are data rows
    expect(rows[1]).toHaveTextContent("Alice");
    expect(rows[2]).toHaveTextContent("Bob");
    expect(rows[3]).toHaveTextContent("Charlie");
  });

  it("sorts descending on second header click", () => {
    render(<DataTable data={data} columns={columns} rowKey={rowKey} />);
    const nameHeader = screen.getByText("Name");
    fireEvent.click(nameHeader); // asc
    fireEvent.click(nameHeader); // desc
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("Charlie");
    expect(rows[3]).toHaveTextContent("Alice");
  });

  it("resets sort on third header click", () => {
    render(<DataTable data={data} columns={columns} rowKey={rowKey} />);
    const nameHeader = screen.getByText("Name");
    fireEvent.click(nameHeader); // asc
    fireEvent.click(nameHeader); // desc
    fireEvent.click(nameHeader); // reset
    // After reset, original order should be restored: Alice, Bob, Charlie
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("Alice");
  });

  it("uses custom render function for cells", () => {
    const customColumns: Column<Row>[] = [
      {
        key: "name",
        header: "Name",
        render: (val) => <span data-testid="custom">{String(val)} (custom)</span>,
      },
    ];
    render(<DataTable data={data} columns={customColumns} rowKey={rowKey} />);
    const cells = screen.getAllByTestId("custom");
    expect(cells[0]).toHaveTextContent("Alice (custom)");
  });

  it("does not render pagination when data fits on one page", () => {
    render(<DataTable data={data} columns={columns} rowKey={rowKey} pageSize={20} />);
    expect(screen.queryByTestId("chevron-left")).not.toBeInTheDocument();
  });

  it("renders pagination when data exceeds pageSize", () => {
    const manyRows = Array.from({ length: 25 }, (_, i) => ({
      id: String(i),
      name: `Item ${i}`,
      value: i,
    }));
    render(<DataTable data={manyRows} columns={columns} rowKey={rowKey} pageSize={10} />);
    expect(screen.getByText(/page 1 of/i)).toBeInTheDocument();
  });
});
