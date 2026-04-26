import { db, schema } from 'hub:db'
import { and, eq } from 'drizzle-orm'

export default defineOAuthGitHubEventHandler({
  async onSuccess(event, { user: ghUser }) {
    const session = await getUserSession(event)

    let user = await db.query.users.findFirst({
      where: () => and(
        eq(schema.users.provider, 'github'),
        eq(schema.users.providerId, ghUser.id.toString())
      )
    })
    if (!user) {
      [user] = await db.insert(schema.users).values({
        id: session.id,
        name: ghUser.name || '',
        email: ghUser.email || '',
        avatar: ghUser.avatar_url || '',
        username: ghUser.login,
        provider: 'github',
        providerId: ghUser.id.toString()
      }).returning()
    }

    await setUserSession(event, { user })

    return sendRedirect(event, '/')
  },
  onError(event, error) {
    console.error('GitHub OAuth error:', error)
    return sendRedirect(event, '/')
  }
})
