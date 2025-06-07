module Jekyll
  class YouTubeEmbed < Liquid::Tag
    def initialize(tag_name, markup, tokens)
      super
      @video_id = markup.strip
    end

    def render(context)
      <<~HTML
        <div class="video-container">
          <iframe 
            src="https://www.youtube.com/embed/#{@video_id}" 
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen>
          </iframe>
        </div>
      HTML
    end
  end
end

Liquid::Template.register_tag('youtube', Jekyll::YouTubeEmbed)
