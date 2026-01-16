from config import db
from app import app
from models.user import User
from models.post import Post
from models.category import Category
from models.comment import Comment
from models.reaction import Reaction
from models.admin_response import AdminResponse

# Drop and create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# ---------------------
# Create categories
# ---------------------
    categories = [
        Category(name="Academics"),
        Category(name="Facilities"),
        Category(name="Events"),
        Category(name="Sports"),
        Category(name="Clubs")
    ]

    for c in categories:
        db.session.add(c)
    db.session.commit()

    # ---------------------
    # Create admin
    # ---------------------
    admin = User(email="admin@campus.com", role="admin")
    admin.set_password("admin123")
    db.session.add(admin)

    # ---------------------
    # Create students
    # ---------------------
    student1 = User(email="student1@campus.com", role="student")
    student1.set_password("password1")
    db.session.add(student1)

    student2 = User(email="student2@campus.com", role="student")
    student2.set_password("password2")
    db.session.add(student2)

    student3 = User(email="student3@campus.com", role="student")
    student3.set_password("password3")
    db.session.add(student3)

    db.session.commit()

    students = [student1, student2, student3]

    # ---------------------
    # Create posts
    # ---------------------
    post1 = Post(content="We need more study groups for Math.", user_id=student1.id, category_id=categories[0].id)
    post2 = Post(content="The library computers are too slow.", user_id=student2.id, category_id=categories[1].id)
    post3 = Post(content="Looking forward to the cultural festival!", user_id=student3.id, category_id=categories[2].id)
    post4 = Post(content="The football field lights are broken.", user_id=student1.id, category_id=categories[3].id)
    post5 = Post(content="How do I join the debate club?", user_id=student2.id, category_id=categories[4].id)

    posts = [post1, post2, post3, post4, post5]

    for p in posts:
        db.session.add(p)
    db.session.commit()

    # ---------------------
    # Add comments
    # ---------------------
    comment1 = Comment(content="Totally agree!", user_id=student2.id, post_id=post1.id)
    comment2 = Comment(content="We need more sessions.", user_id=student3.id, post_id=post1.id)
    comment3 = Comment(content="Great idea!", user_id=student1.id, post_id=post2.id)
    comment4 = Comment(content="I can help organize this.", user_id=student3.id, post_id=post3.id)
    comment5 = Comment(content="Looking forward to it!", user_id=student1.id, post_id=post3.id)

    comments = [comment1, comment2, comment3, comment4, comment5]

    for c in comments:
        db.session.add(c)
    db.session.commit()

    # ---------------------
    # Add reactions
    # ---------------------
    reaction1 = Reaction(post_id=post1.id, user_id=student1.id, reaction_type="like")
    reaction2 = Reaction(post_id=post1.id, user_id=student2.id, reaction_type="like")
    reaction3 = Reaction(post_id=post2.id, user_id=student3.id, reaction_type="dislike")
    reaction4 = Reaction(post_id=post3.id, user_id=student1.id, reaction_type="like")
    reaction5 = Reaction(post_id=post3.id, user_id=student2.id, reaction_type="dislike")

    reactions = [reaction1, reaction2, reaction3, reaction4, reaction5]

    for r in reactions:
        db.session.add(r)
    db.session.commit()

    # ---------------------
    # Add admin responses
    # ---------------------
    response1 = AdminResponse(post_id=post1.id, admin_id=admin.id, content="Thanks for your suggestion. We will organize study groups.")
    response2 = AdminResponse(post_id=post2.id, admin_id=admin.id, content="Library computers will be upgraded next month.")

    responses = [response1, response2]

    for resp in responses:
        db.session.add(resp)
    db.session.commit()

    print("Original database seeded successfully!")
