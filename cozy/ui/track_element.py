from gi.repository import Gtk, Pango, Gst

import cozy.ui
from cozy.control import player as player
from cozy.control.string_representation import seconds_to_str
from cozy.db.book import Book
from cozy.db.track import Track


class TrackElement(Gtk.EventBox):
    """
    An element to display a track in a book popover.
    """
    track = None
    selected = False
    ui = None
    book = None

    def __init__(self, t, book):
        self.track = t
        self.ui = cozy.ui.main_view.CozyUI()
        self.book = book

        super().__init__()
        self.connect("enter-notify-event", self._on_enter_notify)
        self.connect("leave-notify-event", self._on_leave_notify)
        self.connect("button-press-event", self.__on_button_press)
        self.set_tooltip_text(_("Play this part"))
        self.props.width_request = 400

        # This box contains all content
        self.box = Gtk.Box()
        self.box.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.box.set_spacing(3)
        self.box.set_halign(Gtk.Align.FILL)
        self.box.set_valign(Gtk.Align.CENTER)

        # These are the widgets that contain data
        self.play_img = Gtk.Image()
        no_label = Gtk.Label()
        title_label = Gtk.Label()
        dur_label = Gtk.Label()

        self.play_img.set_margin_right(5)
        self.play_img.props.width_request = 16

        no_label.set_text(str(self.track.number))
        no_label.props.margin = 4
        no_label.set_margin_right(7)
        no_label.set_margin_left(0)
        no_label.set_size_request(30, -1)
        no_label.set_xalign(1)

        title_label.set_text(self.track.name)
        title_label.set_halign(Gtk.Align.START)
        title_label.props.margin = 4
        title_label.props.hexpand = True
        title_label.props.hexpand_set = True
        title_label.set_margin_right(7)
        title_label.props.width_request = 100
        title_label.props.xalign = 0.0
        title_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

        dur_label.set_text(seconds_to_str(self.track.length))
        dur_label.get_style_context().add_class("monospace")
        dur_label.set_halign(Gtk.Align.END)
        dur_label.props.margin = 4
        dur_label.set_margin_left(60)

        self.box.add(self.play_img)
        self.box.add(no_label)
        self.box.pack_start(title_label, True, True, 0)
        self.box.pack_end(dur_label, False, False, 0)

        self.add(self.box)

    def __on_button_press(self, eventbox, event):
        """
        Play the selected track.
        """
        current_track = player.get_current_track()

        if current_track and current_track.id == self.track.id:
            player.play_pause(None)
            if player.get_gst_player_state() == Gst.State.PLAYING:
                player.jump_to_ns(Track.select().where(
                    Track.id == self.track.id).get().position)
        else:
            player.load_file(Track.select().where(Track.id == self.track.id).get())
            player.play_pause(None, True)
            Book.update(position=self.track).where(
                Book.id == self.track.book.id).execute()

    def _on_enter_notify(self, widget, event):
        """
        On enter notify add css hover class
        :param widget: as Gtk.EventBox
        :param event: as Gdk.Event
        """
        if self.ui.current_track_element is not self and not self.selected:
            self.play_img.set_from_icon_name(
                "media-playback-start-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.box.get_style_context().add_class("box_hover")
        self.play_img.get_style_context().add_class("box_hover")

    def _on_leave_notify(self, widget, event):
        """
        On leave notify remove css hover class
        :param widget: as Gtk.EventBox (can be None)
        :param event: as Gdk.Event (can be None)
        """
        self.box.get_style_context().remove_class("box_hover")
        self.play_img.get_style_context().remove_class("box_hover")
        if self.ui.current_track_element is not self and not self.selected:
            self.play_img.clear()

    def select(self):
        """
        Select this track as the current position of the audio book.
        Permanently displays the play icon.
        """
        self.book.deselect_track_element()
        self.selected = True
        self.play_img.set_from_icon_name(
            "media-playback-start-symbolic", Gtk.IconSize.SMALL_TOOLBAR)

    def deselect(self):
        """
        Deselect this track.
        """
        self.selected = False
        self.play_img.clear()

    def set_playing(self, playing):
        """
        Update the icon of this track
        :param playing: Is currently playing?
        """
        if playing:
            self.play_img.set_from_icon_name(
                "media-playback-pause-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        else:
            self.play_img.set_from_icon_name(
                "media-playback-start-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
