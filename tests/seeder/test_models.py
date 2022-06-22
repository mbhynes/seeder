import datetime

from seeder.models import PlayerType, Player, Match


class TestPlayer:

  def test_make_with_dependencies(self):
    payload = {"slug": "/doubles-team/o-brien/palmer/"}
    actual = Player.make_with_dependencies(**payload)
    expected = [{
      'slug':         '/player/o-brien/',
      'player_id':    Player.surrogate_key('/player/o-brien/'),
      'player_type':  PlayerType.single,
    }, {
      'slug':         '/player/palmer/',
      'player_id':    Player.surrogate_key('/player/palmer/'),
      'player_type':  PlayerType.single,
    }, {
      'slug':         '/doubles-team/o-brien/palmer/',
      'player_id':    Player.surrogate_key('/doubles-team/o-brien/palmer/'),
      'player_type':  PlayerType.double,
      'p1':           Player.surrogate_key('/player/o-brien/'),
      'p2':           Player.surrogate_key('/player/palmer/'),
    }]
    assert [r.to_partial_dict() for r in actual] == expected


class TestMatch:

  def test_make_with_dependencies(self):
    payload = {
      "tournament":   "/indian-wells/2000/atp-men/",
      "match_number": 55469, 
      "match_at":     datetime.datetime(2000, 3, 19),
      "match_type":   PlayerType.double,
      "is_win_p1":    True,
      "is_win_p2":    False,
      "p1":           "/doubles-team/a/b/",
      "result_p1":    1,
      "sets_p1":      1,
      "score1_p1":    6,
      "p2":           "/player/c/",
      "result_p2":    0,
      "sets_p2":      1,
      "score1_p2":    1,
    }
    actual = Match.make_with_dependencies(**payload)
    expected = [{
      'slug':         '/player/a/',
      'player_id':    Player.surrogate_key('/player/a/'),
      'player_type':  PlayerType.single,
    }, {
      'slug':         '/player/b/',
      'player_id':    Player.surrogate_key('/player/b/'),
      'player_type':  PlayerType.single,
    }, {
      'slug':         '/doubles-team/a/b/',
      'player_id':    Player.surrogate_key('/doubles-team/a/b/'),
      'player_type':  PlayerType.double,
      'p1':           Player.surrogate_key('/player/a/'),
      'p2':           Player.surrogate_key('/player/b/'),
    }, {
      "slug":         '/player/c/',
      "player_id":    Player.surrogate_key("/player/c/"),
      "player_type":  PlayerType.single,
    }, {
      **payload,
      **{
        "match_id":   Match.surrogate_key(55469),
        "p1":         Player.surrogate_key("/doubles-team/a/b/"),
        "p2":         Player.surrogate_key("/player/c/"),
      }
    }]
    assert [r.to_partial_dict() for r in actual] == expected
