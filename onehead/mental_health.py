import random

from discord.member import Member
from discord.ext.commands import Cog, Context, command, has_role

from onehead.common import Roles, get_discord_member_from_name


class MentalHealth(Cog):
    quotes: list[str] = [
        """'It's not whether you get knocked down; it's whether you get up.' — Vince Lombardi""",
        """'The only way to prove that you’re a good sport is to lose.' - Ernie Banks""",
        """'When you’re riding, only the race in which you’re riding is important.' - Bill Shoemaker""",
        """'Age is no barrier. It’s a limitation you put on your mind.'- Jackie Joyner-Kersee""",
        """'Only he who can see the invisible can do the impossible.' - Frank L. Gaines""",
        """'I always felt that my greatest asset was not my physical ability, it was my mental ability.' - Bruce Jenner""",
        """'A trophy carries dust. Memories last forever.' - Mary Lou Retton""",
        """'Number one is just to gain a passion for running. To love the morning, to love the trail, to love the pace on the track. And if some kid gets really good at it, that’s cool too.' - Pat Tyson""",
        """'Most people give up just when they’re about to achieve success. They quit on the one yard line. They give up at the last minute of the game one foot from a winning touchdown.' - Ross Perot""",
        """'You have to do something in your life that is honorable and not cowardly if you are to live in peace with yourself.' - Larry Brown""",
        """'There may be people that have more talent than you, but theres no excuse for anyone to work harder than you do.' - Derek Jeter""",
        """'Baseball is the only field of endeavor where a man can succeed three times out of ten and be considered a good performer.' - Ted Williams""",
        """'One man practicing sportsmanship is far better than 50 preaching it.' - Knute Rockne""",
        """'The five S’s of sports training are: stamina, speed, strength, skill, and spirit; but the greatest of these is spirit.' - Ken Doherty""",
        """'An athlete cannot run with money in his pockets. He must run with hope in his heart and dreams in his head.' - Emil Zatopek""",
        """'Somewhere behind the athlete you’ve become and the hours of practice and the coaches who have pushed you is a little girl who fell in love with the game and never looked back… play for her.' - Mia Hamm""",
        """'When you’ve got something to prove, there’s nothing greater than a challenge.' - Terry Bradshaw""",
        """'Never give up, never give in, and when the upper hand is ours, may we have the ability to handle the win with the dignity that we absorbed the loss.' - Doug Williams""",
        """'It’s not the will to win that matters—everyone has that. It’s the will to prepare to win that matters.' - Paul 'Bear' Bryant""",
        """'Persistence can change failure into extraordinary achievement.' - Marv Levy""",
        """'*unintelligible brummie mutterings*' - Sponge""",
        """'I’ve learned that something constructive comes from every defeat.' - Tom Landry""",
        """'Make sure your worst enemy doesn’t live between your own two ears.' - Laird Hamilton""",
        """'Set your goals high, and don’t stop till you get there.' - Bo Jackson""",
        """'I became a good pitcher when I stopped trying to make them miss the ball and started trying to make them hit it.' - Sandy Koufax""",
        """'If you can’t outplay them, outwork them.' - Ben Hogan""",
        """'People ask me what I do in winter when there’s no baseball. I’ll tell you what I do. I stare out the window and wait for spring.' - Rogers Hornsby""",
        """'Most people never run far enough on their first wind to find out they’ve got a second.' - William James""",
        """'Do you know what my favorite part of the game is? The opportunity to play.' - Mike Singletary""",
        """'If at first you don’t succeed, you are running about average.' - M.H. Alderson""",
        """'Continuous effort — not strength or intelligence — is the key to unlocking our potential.' - Liane Cardes""",
        """'Good is not good when better is expected.' - Vin Scully""",
        """'The difference between the impossible and the possible lies in a person’s determination.' - Tommy Lasorda""",
        """'Champions keep playing until they get it right.' - Billie Jean King""",
        """'You were born to be a player. You were meant to be here. This moment is yours.' - Herb Brooks""",
        """'What you lack in talent can be made up with desire, hustle, and giving 110 percent all the time.' - Don Zimmer""",
        """'If you fail to prepare, you’re prepared to fail.' - Mark Spitz""",
        """'How you respond to the challenge in the second half will determine what you become after the game, whether you are a winner or a loser.' - Lou Holtz""",
        """'Persistence can change failure into extraordinary achievement.' - Matt Biondi""",
        """'Sports serve society by providing vivid examples of excellence.' - George F. Will""",
        """'The principle is competing against yourself. It’s about self-improvement, about being better than you were the day before.' - Steve Young""",
        """'The road to Easy Street goes through the sewer.' - John Madden""",
        """'You are never really playing an opponent. You are playing yourself, your own highest standards, and when you reach your limits, that is real joy.' - Arthur Ashe""",
        """'What makes something special is not just what you have to gain, but what you feel there is to lose.' - Andre Agassi""",
        """'The more difficult the victory, the greater the happiness in winning.' - Pele""",
        """'It ain’t about how hard you can hit. It’s about how hard you can get hit, and keep moving forward.' - Sylvester Stallone, Rocky Balboa""",
        """'Most talented players don’t always succeed. Some don’t even make the team. It’s more what’s inside.' - Brett Favre""",
        """'One man can be a crucial ingredient on a team, but one man cannot make a team. ' - Kareem Abdul-Jabbar""",
        """'Nobody who ever gave his best regretted it.' - George Halas""",
        """'Stubbornness usually is considered a negative; but I think that trait has been a positive for me.' - Cal Ripken Jr.""",
        """'You’ve got to take the initiative and play your game. In a decisive set, confidence is the difference.' - Chris Evert""",
        """'When you win, say nothing, when you lose, say less.' - Paul Brown""",
        """'The hardest skill to acquire in this sport is the one where you compete all out, give it all you have, and you are still getting beat no matter what you do. When you have the killer instinct to fight through that, it is very special.' - Eddie Reese""",
        """'The mind is the limit. As long as the mind can envision the fact that you can do something, you can do it, as long as you really believe 100 percent.' - Arnold Schwarzenegger""",
        """'When I go out there, I have no pity on my brother. I am out there to win.' - Joe Frazier""",
        """'During my 18 years I came to bat almost 10,000 times. I struck out about 1,700 times and walked maybe 1,800 times. You figure a ballplayer will average about 500 at bats a season. That means I played seven years without ever hitting the ball.' - Mickey Mantle""",
        """'I never left the field saying I could have done more to get ready and that gives me peace of mind.' - Peyton Manning""",
        """'Leadership, like coaching, is fighting for the hearts and souls of men and getting them to believe in you.' - Eddie Robinson""",
        """'You win some, you lose some, and some get rained out, but you gotta suit up for them all.' - J. Askenberg""",
        """'Always make a total effort, even when the odds are against you.' - Arnold Palmer""",
        """'You have to expect things of yourself before you can do them.' - Michael Jordan""",
        """'It's fine.' - Zhiyuan Ma""",
        """'To uncover your true potential you must first find your own limits and then you have to have the courage to blow past them.' - Picabo Street""",
        """'Show me a guy who’s afraid to look bad, and I’ll show you a guy you can beat every time.' - Lou Brock""",
        """'You can motivate by fear, and you can motivate by reward. But both those methods are only temporary. The only lasting thing is self motivation.' - Homer Rice""",
        """'You find that you have peace of mind and can enjoy yourself, get more sleep, and rest when you know that it was a one hundred percent effort that you gave-win or lose.' - Gordie Howe""",
        """'If you train hard, you’ll not only be hard, you’ll be hard to beat.' - Herschel Walker""",
        """'My motto was always to keep swinging. Whether I was in a slump or feeling badly or having trouble off the field, the only thing to do was keep swinging.' - Hank Aaron""",
        """'I didn’t believe in team motivation. I believe in getting a team prepared so it knows it will have the necessary confidence when it steps on the field and be prepared to play a good game.' - Tom Landry""",
        """'Your biggest opponent isn’t the other guy. It’s human nature.' - Bobby Knight""",
        """'If you can believe it, the mind can achieve it.' - Ronnie Lott""",
        """'If you don’t have confidence, you’ll always find a way not to win.' - Carl Lewis""",
        """'Without self-discipline, success is impossible, period.' - Lou Holtz""",
        """'Obstacles don’t have to stop you. If you run into a wall, don’t turn around and give up. Figure out how to climb it, go through it, or work around it.' - Michael Jordan""",
        """'Make each day your masterpiece.' - John Wooden""",
        """'Excellence is the gradual result of always striving to do better.' - Pat Riley""",
        """'Win If You Can, Lose If You Must, But NEVER QUIT!' - Cameron Trammell""",
        """'Do you know what my favorite part of the game is? The opportunity to play.' - Mike Singletary""",
        """'If you have everything under control, you’re not moving fast enough.' - Mario Andretti""",
        """'Just keep going. Everybody gets better if they keep at it.' - Ted Williams""",
        """'What do do with a mistake: recognize it, admit it, learn from it, forget it.' - Dean Smith""",
        """'Push yourself again and again. Don’t give an inch until the final buzzer sounds.' - Larry Bird""",
        """'If you aren’t going all the way, why go at all?' - Joe Namath""",
        """'You can’t put a limit on anything. The more you dream, the farther you get.' - Michael Phelps""",
        """'Do not let what you can not do interfere with what you can do.' - John Wooden""",
        """'Pain is temporary. It may last a minute, or an hour, or a day, or a year, but eventually it will subside and something else will take its place. If I quit, however, it lasts forever.' - Lance Armstrong""",
        """'Wisdom is always an overmatch for strength.' - Phil Jackson""",
        """'The will to win is important, but the will to prepare is vital.' - Joe Paterno""",
        """'Adversity cause some men to break; others to break records.' - William A. Ward""",
        """'Never let your head hang down. Never give up and sit down and grieve. Find another way.' - Satchel Paige""",
        """'Some people say I have attitude - maybe I do…but I think you have to. You have to believe in yourself when no one else does - that makes you a winner right there. ' - Venus Williams""",
        """'Never let the fear of striking out get in your way.' - Babe Ruth""",
        """'It is not the size of a man but the size of his heart that matters.' - Evander Holyfield""",
        """'I hated every minute of training, but I said, ‘Don’t quit. Suffer now and live the rest of your life as a champion.’' - Muhammad Ali""",
        """'There are only two options regarding commitment. You’re either IN or you’re OUT. There is no such thing as life in-between.' - Pat Riley""",
        """'A champion is someone who gets up when he can’t.' - Jack Dempsey""",
        """'It ain’t over till it’s over.' - Yogi Berra""",
        """'You’re only as strong as your weakest link.' - Phil Jackson""",
        """'You’re never a loser until you quit trying.' - Mike Ditka""",
        """'Never give up! Failure and rejection are only the first step to succeeding.' - Jim Valvano""",
        """'You miss 100 percent of the shots you don’t take.' - Wayne Gretzky""",
        """'The highest compliment that you can pay me is to say that I work hard every day, that I never dog it.' - Wayne Gretzky""",
        """'Gold medals aren’t really made of gold. They’re made of sweat, determination, and a hard-to-find alloy called guts.' - Dan Gable""",
        """'I’ve missed more than 9,000 shots in my career. I’ve lost almost 300 games. 26 times, I’ve been trusted to take the game winning shot and missed. I’ve failed over and over and over again in my life. And that is why I succeed.' - Michael Jordan""",
        """'It’s not whether you get knocked down; it’s whether you get up.' - Vince Lombardi""",
        """'Push mid and end.' - James Peckham""",
        """'gotta ban the io' - THANOS""",
        """'ZUG ZUG' - Rugor""",
    ]

    @has_role(Roles.MEMBER)
    @command(aliases=["mh"])
    async def mental_health(self, ctx: Context, name: str) -> None:
        """
        Provides mental health to the target player.
        """

        quote: str = random.choice(self.quotes)

        member: Member | None = get_discord_member_from_name(ctx, name)
        if member:
            message: str = f"**{member.mention}**\n {quote}"
        else:
            message: str = f"**{name}**\n {quote}"

        await ctx.send(message)
