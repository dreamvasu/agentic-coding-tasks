# frozen_string_literal: true

module Jekyll
  module Tags
    # {% data_table <name> [columns: a,b,c] [header: true|false] [sort: <col>] [order: asc|desc] %}
    class DataTable < Liquid::Tag
      def initialize(tag_name, markup, tokens)
        super
        @markup = markup.strip
      end

      def render(context)
        site = context.registers[:site]
        page = context.registers[:page]
        opts = parse_markup(@markup)
        name = opts[:name]
        register_dependency(site, page, name)

        rows = site.data[name]
        raise ArgumentError, "data_table: '#{name}' is missing" if rows.nil?
        raise ArgumentError, "data_table: '#{name}' is not a list of maps" unless rows.is_a?(Array)

        columns = opts[:columns] || default_columns(rows)
        build_html(sort_rows(rows, opts), columns, opts)
      end

      private

      def parse_markup(markup)
        name = markup.split(/\s+/).first.to_s
        rest = markup.sub(/\A\s*#{Regexp.escape(name)}\s*/, "")
        opts = { name: name, header: true }
        opts[:columns] = Regexp.last_match(1).split(",") if rest =~ /columns:\s*([\w,\-]+)/
        opts[:sort] = Regexp.last_match(1) if rest =~ /sort:\s*([\w-]+)/
        opts[:order] = Regexp.last_match(1) if rest =~ /order:\s*(asc|desc)/
        opts[:header] = (Regexp.last_match(1) == "true") if rest =~ /header:\s*(true|false)/
        opts
      end

      def default_columns(rows)
        first = rows.first
        first.is_a?(Hash) ? first.keys : []
      end

      def sort_rows(rows, opts)
        return rows unless opts[:sort]

        sorted = rows.sort_by { |row| row.is_a?(Hash) ? row[opts[:sort]] : row }
        opts[:order] == "desc" ? sorted.reverse : sorted
      end

      def build_html(rows, columns, opts)
        out = +"<table>"
        if opts[:header]
          out << "<thead><tr>"
          columns.each { |col| out << "<th>#{col}</th>" }
          out << "</tr></thead>"
        end
        out << "<tbody>"
        rows.each do |row|
          out << "<tr>"
          columns.each { |col| out << "<td>#{row.is_a?(Hash) ? row[col] : row}</td>" }
          out << "</tr>"
        end
        out << "</tbody></table>"
        out
      end

      def register_dependency(site, page, name)
        return unless page&.key?("path")

        file = data_file(site, name)
        return if file.nil?

        site.regenerator.add_dependency(site.in_source_dir(page["path"]), file)
      end

      def data_file(site, name)
        %w(.yml .yaml .json .csv .tsv).each do |ext|
          path = site.in_source_dir("_data", "#{name}#{ext}")
          return path if File.exist?(path)
        end
        nil
      end
    end
  end
end

Liquid::Template.register_tag("data_table", Jekyll::Tags::DataTable)
