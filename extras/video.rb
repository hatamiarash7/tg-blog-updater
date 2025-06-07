module Jekyll
  class VideoTag < Liquid::Tag
    def initialize(tag_name, input, tokens)
      super
      @file = input.strip
    end

    def render(context)
      <<~HTML
        <video controls>
          <source src="/assets/#{@file}" type="video/mp4">
          Your browser does not support the video.
        </video>
      HTML
    end
  end
end

Liquid::Template.register_tag('video', Jekyll::VideoTag)

