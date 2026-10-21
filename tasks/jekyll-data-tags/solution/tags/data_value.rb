# frozen_string_literal: true

module Jekyll
  module Tags
    # {% data_value <name>.<dotted.path> [default: "..."] %}
    class DataValue < Liquid::Tag
      SYNTAX = %r!\A\s*([\w-]+(?:\.[\w-]+)*)\s*(?:default:\s*"([^"]*)")?\s*\z!

      def initialize(tag_name, markup, tokens)
        super
        match = markup.match(SYNTAX)
        raise Liquid::SyntaxError, "Invalid syntax for data_value: #{markup.strip}" unless match

        @path = match[1]
        @default = match[2]
      end

      def render(context)
        site = context.registers[:site]
        page = context.registers[:page]
        segments = @path.split(".")
        name = segments.shift
        register_dependency(site, page, name)

        value = resolve(site.data[name], segments)
        if value.nil?
          return @default unless @default.nil?

          raise ArgumentError, "data_value: path '#{@path}' not found and no default given"
        end
        value.to_s
      end

      private

      def resolve(data, segments)
        segments.reduce(data) do |acc, seg|
          break nil if acc.nil?

          if acc.is_a?(Array)
            idx = Integer(seg, exception: false)
            idx.nil? ? nil : acc[idx]
          elsif acc.is_a?(Hash)
            acc[seg]
          end
        end
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

Liquid::Template.register_tag("data_value", Jekyll::Tags::DataValue)
