# frozen_string_literal: true

module Jekyll
  module Tags
    # {% data_list <name> [field] %}
    class DataList < Liquid::Tag
      def initialize(tag_name, markup, tokens)
        super
        @markup = markup.strip
      end

      def render(context)
        site = context.registers[:site]
        page = context.registers[:page]
        tokens = @markup.split(/\s+/)
        name = tokens.shift
        field = tokens.shift
        register_dependency(site, page, name)

        items = site.data[name]
        raise ArgumentError, "data_list: '#{name}' is missing" if items.nil?
        raise ArgumentError, "data_list: '#{name}' is not a list" unless items.is_a?(Array)

        out = +"<ul>"
        items.each do |item|
          value = field ? (item.is_a?(Hash) ? item[field] : nil) : item
          out << "<li>#{value}</li>"
        end
        out << "</ul>"
        out
      end

      private

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

Liquid::Template.register_tag("data_list", Jekyll::Tags::DataList)
